# Coding Standards

To ensure maintainability and clarity, the following standards must be followed in this project:

## 1. Single Responsibility Principle (SRP)
Each function and class must have **one** specific task. If a function is doing multiple things (e.g., detecting language, calling an API, and formatting the response), it should be broken down.

## 2. Layered Architecture (Backend)
The backend follows a layered approach:
- **API Layer (`backend/api/`)**: Handles HTTP requests, input validation (Pydantic models), and calls services. It should not contain business logic.
- **Service Layer (`backend/app/services/`)**: Contains the core business logic. Orchestrates calls to ML components or data loaders.
- **ML/Core Layer (`backend/app/ml/`, `backend/app/core/`)**: Specialized tools for intent classification, similarity search, and data loading.

## 3. Naming Conventions
- **Python**: Use `snake_case` for functions, variables, and file names. Use `PascalCase` for classes.
- **JavaScript/TypeScript**: Use `camelCase` for functions and variables. Use `PascalCase` for components and classes.

## 4. Error Handling
- Use FastAPI's `HTTPException` in the API layer to return proper status codes to the client.
- Use standard Python exceptions or custom exceptions in the service and core layers.
- Avoid catching generic `Exception` unless logging and re-raising or returning a controlled error.

## 5. Documentation
- All public functions and classes should have a docstring (Python) or JSDoc (TypeScript) explaining their purpose, parameters, and return values.

## 6. Frontend Components
- Break down large components (like `Chat.tsx`) into smaller, reusable sub-components.
- Keep business logic (API calls, complex state transitions) separate from presentation where possible.
