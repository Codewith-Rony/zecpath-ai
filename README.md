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

## Day 5 – Resume Text Extraction Engine

The Day 5 module provides the base resume text extraction pipeline for Zecpath AI.

### Extraction Pipeline

Resume File
    |
    +---- PDF ------> PyMuPDF
    |
    +---- DOCX -----> python-docx
                       |
                       v
                  Raw Text
                       |
                       v
                 Text Cleaner
                       |
                       v
                 Cleaned Text
                       |
                       v
                  JSON Output

### Supported Formats

- PDF
- DOCX

### Features

- Extract text from PDF resumes using PyMuPDF
- Extract text from DOCX resumes using python-docx
- Read DOCX paragraphs and table content
- Normalize bullet characters
- Normalize common resume section headings
- Clean excessive whitespace
- Preserve raw extracted text
- Store raw and cleaned text in JSON format
- Automated pytest tests

### Running the Resume Extraction Engine

Run:

    python main.py

Enter the path to a resume when prompted.

Example:

    data/sample_resumes/sample_resume.pdf

The extracted result is saved inside:

    outputs/

Example output:

    outputs/sample_resume_extracted.json

### Testing

Run the complete test suite:

    pytest

Current test result:

    7 passed

Test results are also stored in:

    test_results.log

### Day 5 Project Structure

    parsers/
    |-- pdf_parser.py
    |-- docx_parser.py
    |-- text_cleaner.py
    `-- resume_extractor.py

    utils/
    `-- file_handler.py

    tests/
    |-- test_basic.py
    |-- test_pdf_parser.py
    |-- test_docx_parser.py
    |-- test_resume_extractor.py
    |-- test_file_handler.py
    `-- test_scoring.py