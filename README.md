# ml-tech-assessment

## Environment Setup

### Using Conda (Recommended)

1. Install Conda if you haven't already:
   - Download and install [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://www.anaconda.com/products/distribution)

2. Create and activate a new conda environment:
   ```bash
   conda create -n ml-assessment python=3.12
   conda activate ml-assessment
   ```

## Installing Poetry and Dependencies

1. Install Poetry using pip:
   ```bash
   pip install poetry
   ```

2. Install project dependencies:
   ```bash
   poetry install
   ```

3. Install dev dependencies (linter, test coverage, async test support):
   ```bash
   poetry install --with dev
   ```

## Environment Variables

1. Create a `.env` file in the root directory of the project
2. Copy the contents of the provided `.env` file into your local `.env` file

## Running the Application

Start the API server:
```bash
poetry run uvicorn app.main:app --reload
```

Or directly:
```bash
poetry run python -m app.main
```

Swagger UI is available at: `http://localhost:8000/docs`

## API Endpoints

| Method | Path | Description | Status Codes |
|--------|------|-------------|--------------|
| POST | `/api/v1/transcripts/analyze` | Analyze a single transcript | 201, 422, 502 |
| GET | `/api/v1/transcripts/{analysis_id}` | Get analysis by ID | 200, 404 |
| POST | `/api/v1/transcripts/analyze/batch` | Analyze multiple transcripts concurrently | 201, 422, 502 |

## Running Tests

To run the tests, make sure you have:
1. Activated your virtual environment
2. Installed all dependencies using Poetry
3. Created and populated the `.env` file

Then run:
```bash
pytest
```

For more detailed test output:
```bash
pytest -v
```

For test coverage report:
```bash
pytest --cov
```

## Linting and Formatting

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting:

```bash
ruff check .
ruff format .
```
