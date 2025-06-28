# 🛠 ChatBot-Ai Full Setup Guide

This guide provides a complete setup for running the ChatBot-Ai project from scratch, including all dependencies like Redis, Ollama, and GitHub SSH integration.

---

## 📦 1. Install System Dependencies

Run this in your terminal:

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git redis-server curl
🧠 2. (Optional) Install Ollama (for local LLM like LLaMA3)
bash
Copy
Edit
curl -fsSL https://ollama.com/install.sh | sh
ollama run llama3
🐍 3. Set Up Python Virtual Environment
bash
Copy
Edit
python3 -m venv myenv
source myenv/bin/activate
📂 4. Install Python Dependencies
bash
Copy
Edit
pip install -r requirements.txt
🗃️ 5. Initialize the SQLite Database
bash
Copy
Edit
python init_db.py
Optional: Seed users

bash
Copy
Edit
python seed_users.py
🚀 6. Run the Application
Run the FastAPI server:

bash
Copy
Edit
python server.py
Then open: http://127.0.0.1:8000

Optional: Run webhook receiver

bash
Copy
Edit
python webhook_receiver.py
📊 7. Redis Setup
Start Redis server:

bash
Copy
Edit
sudo service redis-server start
To enable on boot:

bash
Copy
Edit
sudo systemctl enable redis-server
