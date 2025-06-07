from pydantic import BaseModel
from typing import List, Optional

class User(BaseModel):
    id: int
    name: str
    email: str
    balance: float

class Transaction(BaseModel):
    id: int
    user_id: int
    amount: float
    transaction_type: str  
    timestamp: str

class Account(BaseModel):
    id: int
    user_id: int
    account_type: str  
    balance: float

class UserCreate(BaseModel):
    name: str
    email: str

class TransactionCreate(BaseModel):
    user_id: int
    amount: float
    transaction_type: str

class AccountCreate(BaseModel):
    user_id: int
    account_type: str