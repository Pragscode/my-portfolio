# Banking Application Backend

This directory contains the backend implementation of the banking application using FastAPI.

## Project Structure

- **app/**: Contains the main application code.
  - **main.py**: Entry point for the FastAPI application.
  - **models.py**: Pydantic models for request and response validation.
  - **routes/**: Directory for API route definitions.
    - **__init__.py**: Marks the routes directory as a package.
  - **schemas.py**: Data transfer objects (DTOs) for communication between frontend and backend.
  - **utils.py**: Utility functions for the backend application.

## Installation

To set up the backend, ensure you have Python installed, then install the required dependencies:

```bash
pip install -r requirements.txt
```

## Running the Application

To run the FastAPI application, execute the following command:

```bash
uvicorn app.main:app --reload
```

This will start the server at `http://127.0.0.1:8000`. You can access the interactive API documentation at `http://127.0.0.1:8000/docs`.

## Usage

You can use the API endpoints defined in the `routes` directory to interact with the banking application. Refer to the API documentation for details on available endpoints and their usage.