from sqlalchemy.orm import Session
from database import SessionLocal
from models import User
from passlib.context import CryptContext
from uuid import uuid4

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def seed():
    db = SessionLocal()
    db.query(User).delete()
    db.commit()

    users = [
        {
            "username": "aaditya",
            "full_name": "Aaditya Ranjan Moitra",
            "email": "aadityaranjanmoitra@gmail.com",
            "password": "aadipass",
            "disabled": False,
            "uuid": "aaditya-static-uuid",
        },
        {
            "username": "priyanshu",
            "full_name": "Priyanshu Nayak",
            "email": "priyanshunayak@gmail.com",
            "password": "test123",
            "disabled": False,
            "uuid": "priyanshu-static-uuid",
        },
        {
            "username": "user2",
            "full_name": "Second User",
            "email": "user2@example.com",
            "password": "user2password",
            "disabled": False,
            "uuid": "user2-static-uuid",
        },
    ]

    for user_data in users:
        user = User(
            username=user_data["username"],
            full_name=user_data["full_name"],
            email=user_data["email"],
            hashed_password=pwd_context.hash(user_data["password"]),
            disabled=user_data["disabled"],
            uuid=user_data["uuid"],
        )
        db.add(user)
    db.commit()
    db.close()

if __name__ == "__main__":
    seed()
    print("Seeded users.")