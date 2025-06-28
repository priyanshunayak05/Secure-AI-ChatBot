from fastapi import FastAPI, Request
import logging

app = FastAPI()
logging.basicConfig(level=logging.INFO)

@app.post("/webhook/receive")
async def receive_webhook(request: Request):
    payload = await request.json()
    logging.info(f"Webhook received: {payload}")
    return {"status":"received"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1",port=9000)

    