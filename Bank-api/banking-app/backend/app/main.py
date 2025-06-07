import string
import random
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from decimal import Decimal
from typing import Optional
from fastapi import Body, FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer
import mysql.connector
import bcrypt
from datetime import datetime, timedelta
from jose import JWTError, jwt

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, in production specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="register")

SECRET_KEY = "76c53e7bf5fb69ce2cc8d7a2acefe898b36b1262e81af1cd9628fffccdeb2be6d9e25e37f570416b0af7ce86d6287c9206676900f40f06ae3ba20fa577d99ff8"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 3


class UserRegister(BaseModel):
    name: str
    email: str
    password: str
    phone: str
    address: str


class TransactionInput(BaseModel):
    type: str 
    amount: float


class TempPasswordInput(BaseModel):
    account_number: str
    temporary_password: str


class LoginInput(BaseModel):
    account_number: str
    password: str

class PaymentOut(BaseModel):
    id: int
    name: str
    email: str
    account_number: str
    balance: float

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=5))
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token


def account_number_generator():
    length = random.randint(11, 16)
    return ''.join([str(random.randint(0, 9)) for _ in range(length)])


def generate_password(length=10):
    if length < 6:
        raise ValueError("Password length should be at least 6 characters")
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(chars) for _ in range(length))


def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Pa@29042007",
        database="demo"
    )


@app.post("/register")
def register_user(user: UserRegister):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        hashed_pw = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt()).decode()

        cursor.execute(
            "INSERT INTO users (name, email, password, phone, address) VALUES (%s, %s, %s, %s, %s)",
            (user.name, user.email, hashed_pw, user.phone, user.address)
        )

        conn.commit()
        access_token = create_access_token(data={"sub": user.email})

        cursor.close()
        conn.close()

        return JSONResponse(
            content={"message": "User registered successfully!", "access_token": access_token},
            status_code=201
        )

    except mysql.connector.IntegrityError:
        return JSONResponse(content={"error": "Email already registered"}, status_code=400)
    except mysql.connector.Error as e:
        return JSONResponse(content={"error": f"Internal server error: {str(e)}"}, status_code=500)


@app.post("/account_number")
def generate_account_number(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT account_number FROM users WHERE email = %s", (email,))
        result = cursor.fetchone()

        if result and result["account_number"]:
            return {
                "message": "Account number already generated.",
                "account_number": result["account_number"]
            }

        new_acc_num = account_number_generator()
        temp_pw = generate_password()

        cursor.execute(
            "UPDATE users SET account_number = %s, temp_password = %s WHERE email = %s",
            (new_acc_num, temp_pw, email)
        )
        conn.commit()

        cursor.close()
        conn.close()

        return {
            "message": "Account created successfully.",
            "account_number": new_acc_num,
            "temporary_password": temp_pw
        }

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.post("/account_number/per-password")
def get_per_password(data: TempPasswordInput):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT temp_password, permanent_password FROM users WHERE account_number = %s",
            (data.account_number,)
        )
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="Account not found.")

        if user["permanent_password"]:
            return {"message": "Permanent password already generated. Use that to login."}

        if user["temp_password"] != data.temporary_password:
            raise HTTPException(status_code=401, detail="Invalid temporary password.")

        permanent_password = ''.join(random.choices(string.digits, k=5))

        cursor.execute(
            "UPDATE users SET permanent_password = %s, temp_password = NULL WHERE account_number = %s",
            (permanent_password, data.account_number)
        )
        conn.commit()

        cursor.close()
        conn.close()

        return {
            "message": "Permanent password generated successfully.",
            "permanent_password": permanent_password
        }

    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.post("/login")
def login_user(data: LoginInput):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT email, permanent_password FROM users WHERE account_number = %s",
            (data.account_number,)
        )
        user = cursor.fetchone()

        if not user or user["permanent_password"] != data.password:
            raise HTTPException(status_code=401, detail="Invalid account number or password.")

        access_token = create_access_token(data={"sub": user["email"]})

        cursor.close()
        conn.close()

        return {
            "message": "Login successful.",
            "access_token": access_token
        }

    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/myaccount")
def get_account_info(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT id, name, email, account_number, balance FROM users WHERE email = %s", (email,)
        )
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        cursor.execute(
            "SELECT type, amount, transaction_date FROM transactions WHERE user_id = %s ORDER BY transaction_date DESC",
            (user["id"],)
        )
        transactions = cursor.fetchall()

        cursor.close()
        conn.close()

        return {
            "message": "Account info retrieved successfully",
            "account": {
                "name": user["name"],
                "email": user["email"],
                "account_number": user["account_number"],
                "balance": user["balance"],
                "transactions": transactions
            }
        }

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/payment")
def payment():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT id, name, email, account_number, balance FROM users"
        )
        users = cursor.fetchall()

        cursor.close()
        conn.close()

        return {
            "message": "Payment info retrieved successfully",
            "users": users
        }

    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.post("/myaccount")
def post_transaction(
    token: str = Depends(oauth2_scheme),
    transaction: TransactionInput = Body(...),
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT id, name, email, account_number, balance FROM users WHERE email = %s", (email,)
        )
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if transaction.type not in ["deposit", "withdrawal"]:
            raise HTTPException(status_code=400, detail="Invalid transaction type")

        if transaction.amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be greater than zero")

        if transaction.type == "withdrawal":
            if user["balance"] < transaction.amount:
                raise HTTPException(status_code=400, detail="Insufficient balance")
            new_balance = user["balance"] - Decimal(transaction.amount)
        else:
            new_balance = user["balance"] + Decimal(transaction.amount)


        cursor.execute(
            "UPDATE users SET balance = %s WHERE id = %s", (new_balance, user["id"])
        )

        cursor.execute(
            "INSERT INTO transactions (user_id, type, amount) VALUES (%s, %s, %s)",
            (user["id"], transaction.type, transaction.amount)
        )
        conn.commit()

        cursor.close()
        conn.close()

        return {
            "message": f"{transaction.type.capitalize()} successful",
            "new_balance": new_balance
        }

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


if __name__ == '__main__':
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
