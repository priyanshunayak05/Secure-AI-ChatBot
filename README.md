# 🤖 ChatBot-AI

ChatBot-AI is an intelligent chatbot backend designed using Python and FastAPI. It features a clean authentication system, database integration, and webhook handling. This lightweight and modular setup is ideal for building AI-driven conversational interfaces and integrating with local or cloud-based LLMs. It’s perfect for developers looking to build custom chat experiences with full control over logic, data, and user sessions.

![ChatBot UI]()


## 📁 Project Structure

```
ChatBot-Ai-main/
├── server.py # FastAPI app
├── database.py # SQLite DB connection
├── models.py # ORM models
├── init_db.py # DB schema setup
├── seed_users.py # Optional: preloads users
├── webhook_receiver.py # Optional: webhook handler
├── requirements.txt # Python dependencies
├── run.sh # Launch script
├── test.db # SQLite database
```

## ⚙️ Requirements

- Python 3.10 or higher
- `pip` (Python package installer)
- (Optional but recommended) `virtualenv` for isolated environments

## 🛠️ Setup Instructions

### 1. Clone or Extract the Repository

If you're using the `.zip`, simply extract it and `cd` into the project directory:

```bash
cd ChatBot-Ai-main
```

### 2. Set Up Virtual Environment

(Optional but recommended)

```bash
python3 -m venv env
source env/bin/activate   # On Windows use: env\Scripts\activate
```
to write .env file
'''
ACCESS_TOKEN_EXPIRE_MINUTES=30,

SECRET_KEY =your_secret_key_here,

ALGORITHM=HS256
'''

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Initialize the Database

```bash
python init_db.py
```

This creates a SQLite database `test.db` with required tables.

### 5. (Optional) Seed Initial User Data

```bash
python seed_users.py
```

### 6. Run the Server

```bash
python server.py
```

This starts the FastAPI app locally. You can access it at:

```
http://127.0.0.1:8000
```

### 7. Run Webhook Receiver (If applicable)

```bash
python webhook_receiver.py
```

This might be used for receiving external POST data.

## 🧪 Run Tests or CI

If you're integrating with GitHub Actions, `.github/workflows/integration.yml` includes a basic test setup for automation.

## 🔧 Scripts

- `run.sh` – Custom shell script to launch the project (modify as needed)

## 📄 Notes

- The project uses SQLite (`test.db`) for storage. You can replace it with another DB if needed.
- The virtual environment (`env/`) is included but can be deleted and recreated.
- `__pycache__/` includes compiled Python bytecode files.

## 🤖 Features

- FastAPI-based chatbot backend
- SQLite integration
- Webhook support
- Ready for CI/CD integration via GitHub Actions
