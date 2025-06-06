import os
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
import mysql.connector
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from dotenv import load_dotenv
import secrets

load_dotenv()

app = FastAPI()

# Database connection
db = mysql.connector.connect(
    host="your_host",
    user="your_user",
    password="your_password",
    database="your_database"
)
cursor = db.cursor(dictionary=True)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Email configuration
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT")),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_FROM_NAME=os.getenv("MAIL_FROM_NAME"),
    MAIL_TLS=True,
    MAIL_SSL=False,
    USE_CREDENTIALS=True
)

class SignupRequest(BaseModel):
    email: EmailStr
    password: str

# Function to get user by email
def get_user(email):
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    return cursor.fetchone()

# Function to create user with verification token
def create_user(email, password):
    hashed_password = pwd_context.hash(password)
    verification_token = secrets.token_hex(16)  # Generate a random token
    cursor.execute("INSERT INTO users (email, password, verified, verification_token) VALUES (%s, %s, %s, %s)",
                   (email, hashed_password, 0, verification_token))
    db.commit()
    return verification_token

# Send verification email
async def send_verification_email(email, token):
    verification_link = f"http://127.0.0.1:8000/verify/{token}"
    message = MessageSchema(
        subject="Verify Your Email",
        recipients=[email],
        body=f"Click the link to verify your email: {verification_link}",
        subtype="html"
    )
    fm = FastMail(conf)
    await fm.send_message(message)

@app.post("/signup")
async def signup(request: SignupRequest):
    if get_user(request.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    token = create_user(request.email, request.password)
    await send_verification_email(request.email, token)
    
    return {"message": "User registered successfully. Please check your email to verify your account."}

# Verify user email
@app.get("/verify/{token}")
def verify_email(token: str):
    cursor.execute("SELECT * FROM users WHERE verification_token = %s", (token,))
    user = cursor.fetchone()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")

    cursor.execute("UPDATE users SET verified = 1, verification_token = NULL WHERE verification_token = %s", (token,))
    db.commit()
    
    return {"message": "Email verified successfully! You can now log in."}


#Password reset

class ResetPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordConfirm(BaseModel):
    token: str
    new_password: str

# Generate reset token and send email
async def send_reset_email(email, token):
    reset_link = f"http://127.0.0.1:8000/reset-password/{token}"
    message = MessageSchema(
        subject="Reset Your Password",
        recipients=[email],
        body=f"Click the link to reset your password: {reset_link}",
        subtype="html"
    )
    fm = FastMail(conf)
    await fm.send_message(message)

@app.post("/forgot-password")
async def forgot_password(request: ResetPasswordRequest):
    user = get_user(request.email)
    if not user:
        raise HTTPException(status_code=400, detail="Email not found")

    reset_token = secrets.token_hex(16)
    cursor.execute("UPDATE users SET verification_token = %s WHERE email = %s", (reset_token, request.email))
    db.commit()

    await send_reset_email(request.email, reset_token)
    return {"message": "Password reset link sent to your email"}

# Reset password
@app.post("/reset-password")
def reset_password(request: ResetPasswordConfirm):
    cursor.execute("SELECT * FROM users WHERE verification_token = %s", (request.token,))
    user = cursor.fetchone()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    hashed_password = pwd_context.hash(request.new_password)
    cursor.execute("UPDATE users SET password = %s, verification_token = NULL WHERE verification_token = %s", (hashed_password, request.token))
    db.commit()

    return {"message": "Password reset successfully. You can now log in."}

