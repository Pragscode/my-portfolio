import pytest
import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from httpx import AsyncClient
from main import app


@pytest.mark.asyncio
async def test_register_user():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/register", json={
            "name": "Test User",
            "email": "testuser@example.com",
            "password": "Password123!",
            "phone": "1234567890",
            "address": "Test Street"
        })

    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data

if __name__ == '__main__':
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)