import os
import logging
import asyncio
import aiohttp
import json
import time
import redis.asyncio as redis
from uuid import uuid4
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, Depends, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime, timedelta, UTC
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base, User
from dotenv import load_dotenv
import httpx
from contextlib import asynccontextmanager

# Load environment variables
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

if not SECRET_KEY or not ALGORITHM:
    raise RuntimeError("SECRET_KEY and ALGORITHM must be set in environment variables.")

# Webhook URL
WEBHOOK_URL = "https://webhook.site/821d8679-eeda-49a7-87a5-2eeb93ad706f"

# Logging setup
logging.basicConfig(
    filename="my_app.log",
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# FastAPI lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created.")
    yield
    logger.info("Shutting down FastAPI app...")

app = FastAPI(lifespan=lifespan)

# Middleware & static files
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Auth setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth_2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Token(BaseModel):
    access_token: str
    token_type: str
    user_uuid: str

class TokenData(BaseModel):
    username: str | None = None

class UserOut(BaseModel):
    username: str
    full_name: str | None = None
    email: str | None = None
    disabled: bool | None = None
    uuid: str

async def send_webhook(event: dict):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(WEBHOOK_URL, json=event)
            logger.info(f"Webhook sent: status={response.status_code}")
        except Exception as e:
            logger.error(f"Webhook failed: {e}")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_user(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def authenticate_user(db: Session, username: str, password: str):
    user = get_user(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(UTC) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth_2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.warning("JWT decode failed: username missing")
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        logger.warning("JWTError during token validation")
        raise credentials_exception
    user = get_user(db, username=token_data.username)
    if user is None:
        logger.warning(f"User not found: {token_data.username}")
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        logger.info(f"Inactive user tried to access: {current_user.username}")
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.info(f"Failed login attempt for username: {form_data.username}")
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    logger.info(f"User logged in: {user.username} (uuid: {user.uuid})")
    await send_webhook({
        "event": "user_login",
        "username": user.username,
        "uuid": user.uuid,
        "timestamp": datetime.utcnow().isoformat()
    })
    return {"access_token": access_token, "token_type": "bearer", "user_uuid": user.uuid}

@app.get("/users/me/", response_model=UserOut)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    logger.info(f"User profile accessed: {current_user.username}")
    return current_user

# Redis & WebSocket Chat
REDIS_URL = "redis://localhost:6379/0"
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.generation_tasks: dict[str, asyncio.Task] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        await websocket.send_json({"type": "session_id", "session_id": session_id})
        logger.info(f"WebSocket connected: session_id={session_id}")

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        task = self.generation_tasks.pop(session_id, None)
        if task and not task.done():
            task.cancel()
        logger.info(f"WebSocket disconnected: session_id={session_id}")

    async def send_message(self, message: dict, session_id: str):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(message)

    def set_task(self, session_id: str, task: asyncio.Task):
        self.generation_tasks[session_id] = task

    def stop_task(self, session_id: str):
        task = self.generation_tasks.get(session_id)
        if task and not task.done():
            task.cancel()
            logger.info(f"Generation task stopped: session_id={session_id}")
            return True
        return False

manager = ConnectionManager()

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "mistral"

def session_key(uuid, session_id): return f"chat:{uuid}:{session_id}"
def session_meta_key(uuid, session_id): return f"chatmeta:{uuid}:{session_id}"

async def append_history(uuid, session_id, role, content):
    entry = {"role": role, "content": content, "timestamp": int(time.time())}
    await redis_client.rpush(session_key(uuid, session_id), json.dumps(entry))
    meta = await redis_client.hgetall(session_meta_key(uuid, session_id))
    if role == "user":
        await redis_client.hset(session_meta_key(uuid, session_id), mapping={
            "session_id": session_id,
            "title": content[:32] if not meta.get("title") else meta["title"],
            "preview": content[:64],
            "updated_at": str(int(time.time()))
        })
    elif role == "assistant":
        await redis_client.hset(session_meta_key(uuid, session_id), mapping={
            "session_id": session_id,
            "preview": content[:64],
            "updated_at": str(int(time.time()))
        })
    logger.info(f"History appended: uuid={uuid}, session_id={session_id}, role={role}")

async def get_history(uuid, session_id):
    entries = await redis_client.lrange(session_key(uuid, session_id), 0, -1)
    return [json.loads(e) for e in entries]

async def ensure_system_message(uuid, session_id):
    if await redis_client.llen(session_key(uuid, session_id)) == 0:
        await append_history(uuid, session_id, "system", "You are a helpful assistant.")

async def get_all_sessions(uuid):
    keys = await redis_client.keys(f"chatmeta:{uuid}:*")
    sessions = []
    for key in keys:
        meta = await redis_client.hgetall(key)
        if meta:
            sessions.append(meta)
    sessions.sort(key=lambda x: int(x.get("updated_at", "0")), reverse=True)
    return sessions

async def generate_with_ollama(uuid, session_id, websocket: WebSocket):
    await ensure_system_message(uuid, session_id)
    history = await get_history(uuid, session_id)
    payload = {"model": MODEL_NAME, "messages": history, "stream": True}
    full_response = ""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(OLLAMA_URL, json=payload) as resp:
                async for line in resp.content:
                    if not line or line == b"\n": continue
                    try:
                        data = json.loads(line.decode("utf-8"))
                        chunk = data.get("message", {}).get("content", "")
                        full_response += chunk
                        await websocket.send_json({"type": "response_chunk", "content": chunk})
                    except Exception as e:
                        logger.error(f"Error parsing Ollama chunk: {e}")
                await append_history(uuid, session_id, "assistant", full_response)
                await websocket.send_json({"type": "response_end"})
                logger.info(f"Model response completed: uuid={uuid}, session_id={session_id}")
    except asyncio.CancelledError:
        if full_response.strip():
            await append_history(uuid, session_id, "assistant", full_response)
            logger.info(f"Model response stopped and partial saved: uuid={uuid}, session_id={session_id}")
        await websocket.send_json({"type": "stopped"})
    except Exception as e:
        logger.error(f"Error in generate_with_ollama: {e}")
        await websocket.send_json({"type": "error", "content": str(e)})

@app.websocket("/api/chat")
async def websocket_endpoint(websocket: WebSocket, uuid: str = Query(...), session_id: str = Query(None)):
    if not session_id:
        session_id = str(uuid4())
    await ensure_system_message(uuid, session_id)
    try:
        await manager.connect(websocket, session_id)
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("type") == "user_message":
                    manager.stop_task(session_id)
                    await append_history(uuid, session_id, "user", message["content"])
                    logger.info(f"User message received: uuid={uuid}, session_id={session_id}")
                    task = asyncio.create_task(generate_with_ollama(uuid, session_id, websocket))
                    manager.set_task(session_id, task)
                elif message.get("type") == "stop_generation":
                    if manager.stop_task(session_id):
                        await manager.send_message({"type": "stopped"}, session_id)
                        logger.info(f"Stop requested by user: uuid={uuid}, session_id={session_id}")
            except json.JSONDecodeError:
                logger.warning("Received invalid JSON on WebSocket")
    except WebSocketDisconnect:
        manager.disconnect(session_id)
        logger.info(f"WebSocketDisconnect: session_id={session_id}")
    except Exception as e:
        manager.disconnect(session_id)
        logger.error(f"WebSocket error: {e}")

@app.get("/")
def serve_index():
    return FileResponse("static/index.html")

@app.get("/chat.html")
def serve_chat():
    return FileResponse("static/chat.html")

@app.get("/history_sessions")
async def history_sessions(uuid: str):
    sessions = await get_all_sessions(uuid)
    logger.info(f"History sessions fetched for uuid={uuid}")
    return sessions

@app.get("/history/{session_id}")
async def get_history_api(session_id: str, uuid: str):
    history = await get_history(uuid, session_id)
    logger.info(f"History fetched: uuid={uuid}, session_id={session_id}")
    return JSONResponse(content={"session_id": session_id, "history": history})

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI server...")
    uvicorn.run(app, host="127.0.0.1", port=8000)
