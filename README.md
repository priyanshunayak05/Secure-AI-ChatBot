# ChatBot-Ai

A Python-based chatbot server that supports basic user management, webhook communication, and a simple database.

## 📁 Project Structure

```
ChatBot-Ai-main/
├── .gitignore
├── database.py
├── init_db.py
├── models.py
├── requirements.txt
├── run.sh
├── seed_users.py
├── server.py
├── test.db
├── webhook_receiver.py
├── .github/workflows/integration.yml
├── env/                # Python virtual environment (optional, can recreate)
├── __pycache__/        # Compiled Python files
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
