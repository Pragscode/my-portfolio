from pydantic import BaseModel
from typing import List, Optional

class User(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None

class Account(BaseModel):
    id: int
    user_id: int
    account_type: str
    balance: float

class Transaction(BaseModel):
    id: int
    account_id: int
    amount: float
    transaction_type: str  # e.g., 'deposit' or 'withdrawal'
    timestamp: str  # ISO format datetime string

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str

class AccountCreate(BaseModel):
    user_id: int
    account_type: str

class TransactionCreate(BaseModel):
    account_id: int
    amount: float
    transaction_type: str