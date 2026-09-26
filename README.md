# Zecpath AI

AI-powered hiring platform project developed as part of the Zecser Business internship.

## Project Structure

zecpath-ai/
|-- ats_engine/
|-- data/
|-- interview_ai/
|-- parsers/
|-- screening_ai/
|-- scoring/
|-- tests/
|-- utils/
|-- .env.example
|-- .gitignore
|-- main.py
|-- README.md
|-- requirements.txt

## Environment Setup

### 1. Create a virtual environment

    python -m venv venv

### 2. Activate the virtual environment

Windows PowerShell:

    .\venv\Scripts\Activate.ps1

### 3. Install dependencies

    pip install pytest python-dotenv

## Running the Application

    python main.py

## Running Tests

Run all tests using:

    pytest

## Logging

Application logs are stored in:

    logs/app.log

The logging system records application events with timestamps and log levels.

## AI Service Modules

The project is organized into separate modules for:

- Resume parsing
- ATS processing
- AI screening
- AI interviews
- Scoring and decision processing

These modules will be expanded as the project development progresses.

## Development Standards

- Follow Python naming conventions.
- Keep modules focused on a single responsibility.
- Write tests for implemented functionality.
- Use meaningful variable and function names.
- Add comments or documentation where necessary.
- Do not commit .env files or the virtual environment.
- Keep sensitive credentials outside the source code.

## Current Status

Initial Python development environment and project structure have been configured.

Automated tests are configured using pytest.