# Grafana Dashboard Generator - Backend

This is the backend component for the Grafana Dashboard Generator, which uses LangGraph to create and validate Grafana dashboard JSON configurations based on natural language prompts.

## Features

- **LangGraph Agent**: Automatic generation of Grafana dashboard JSON with validation and error correction
- **Retrieval-Augmented Generation (RAG)**: Enhance prompts with relevant context for better results
- **Human-in-the-Loop**: Request human intervention when validation fails after multiple retry attempts
- **Multiple LLM Support**: Integration with OpenAI, Anthropic, and other LLM providers
- **Validation**: Schema validation and error correction for Grafana dashboard JSON

## Setup

### Prerequisites

- Python 3.10+
- OpenAI API key (or Anthropic API key if using Claude)
- [uv](https://github.com/astral-sh/uv) package manager

### Installation

1. Create a virtual environment:

```bash
cd backend
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:

```bash
uv pip install .
```

3. Set up environment variables by creating a `.env` file:

```
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key  # Optional if using Claude
```

## Running the API

Start the FastAPI server:

```bash
python run_api.py
```

The API will be available at http://localhost:8000.

You can access the API documentation at http://localhost:8000/docs.

## API Endpoints

- `POST /api/dashboards/generate`: Generate a dashboard from a natural language prompt
- `GET /api/tasks/{task_id}`: Get the status of a dashboard generation task
- `POST /api/tasks/{task_id}/feedback`: Submit human feedback for a dashboard
- `GET /api/models`: List available LLM models
- `GET /api/health`: Health check endpoint

## Project Structure

- `app/` - Main application code
  - `agents/` - LangGraph agent implementation
  - `schemas/` - Pydantic models and JSON schemas
  - `utils/` - Utility functions
  - `rag/` - Retrieval-Augmented Generation components
  - `main.py` - FastAPI application

## Development

To run tests:

```bash
uv pip install '.[dev]'
pytest
```
