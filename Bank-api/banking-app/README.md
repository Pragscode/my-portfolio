# Banking Application

This project is a banking application that consists of a Tkinter frontend and a FastAPI backend. The application allows users to perform banking operations through a user-friendly interface and a robust API.

## Project Structure

```
banking-app
├── backend
│   ├── app
│   │   ├── main.py          # Entry point for the FastAPI backend
│   │   ├── models.py        # Pydantic models for request/response validation
│   │   ├── routes           # Directory for API routes
│   │   │   └── __init__.py  # Marks routes as a package
│   │   ├── schemas.py       # Data transfer objects (DTOs)
│   │   └── utils.py         # Utility functions for backend
│   ├── requirements.txt      # Backend dependencies
│   └── README.md            # Backend documentation
├── frontend
│   ├── main.py              # Entry point for the Tkinter frontend
│   ├── components           # Directory for UI components
│   │   ├── __init__.py      # Marks components as a package
│   │   └── widgets.py       # Definitions of Tkinter widgets
│   ├── assets               # Directory for styling assets
│   │   └── styles.py        # Styles and themes for the application
│   └── README.md            # Frontend documentation
└── README.md                # Main project documentation
```

## Setup Instructions

### Backend

1. Navigate to the `backend` directory.
2. Install the required dependencies using:
   ```
   pip install -r requirements.txt
   ```
3. Run the FastAPI application:
   ```
   uvicorn app.main:app --reload
   ```

### Frontend

1. Navigate to the `frontend` directory.
2. Run the Tkinter application:
   ```
   python main.py
   ```

## Usage Guidelines

- The backend API can be accessed at `http://localhost:8000`.
- The frontend application provides a graphical interface for interacting with the backend services.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any enhancements or bug fixes.