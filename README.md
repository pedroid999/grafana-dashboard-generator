# Integrated AI-Driven Grafana Dashboard Generator

An end-to-end system that automatically generates and updates Grafana dashboards based on natural language prompts and contextual data.

## Overview

This project consists of two main components:

1. **Backend Agent (LangGraph)**
   - Generates Grafana dashboard JSON from natural language prompts
   - Validates JSON against Grafana schema
   - Implements retry mechanisms for fixing validation issues
   - Incorporates RAG for enhanced context
   - Includes human-in-the-loop for dashboard refinement

2. **Frontend (Next.js with Hexagonal Architecture)**
   - Interactive UI for creating and refining prompts
   - Model selector for choosing among different LLM providers
   - On-screen guidance for creating effective prompts
   - Live preview of generated dashboard JSON
   - Interface for human intervention when needed

## Features

- **Natural Language to Dashboard**: Generate complex Grafana dashboards using simple language
- **Multiple LLM Support**: Choose from OpenAI, Anthropic Claude, and other providers
- **Validation & Auto-correction**: Automatic validation and correction of dashboard JSON
- **Enhanced Context with RAG**: Relevant technical context included in prompt processing
- **Human-in-the-Loop**: Opportunity for manual correction when automatic validation fails
- **Modern React UI**: Clean, responsive interface built with Next.js and Tailwind CSS

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 16+
- OpenAI API key (and optionally Anthropic API key)
- [uv](https://github.com/astral-sh/uv) package manager

### Backend Setup

1. Set up environment and install dependencies:

```bash
cd backend
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install .
```

2. Create a `.env` file with your API keys:

```
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key  # Optional
```

3. Start the backend server:

```bash
python run_api.py
```

The API will be available at http://localhost:8000.

### Frontend Setup

1. Install dependencies:

```bash
cd frontend
npm install
```

2. Create a `.env.local` file:

```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

3. Start the development server:

```bash
npm run dev
```

The application will be available at http://localhost:3000.

## Project Structure

- `backend/`: LangGraph agent and API
  - `app/`: Main application code
    - `agents/`: LangGraph agent implementation
    - `schemas/`: Pydantic models and JSON schemas
    - `utils/`: Utility functions
    - `rag/`: Retrieval-Augmented Generation components
    - `main.py`: FastAPI application

- `frontend/`: Next.js frontend
  - `app/`: Main application code
    - `adapters/`: External adapters (API clients)
    - `components/`: Reusable UI components
    - `domain/`: Domain logic and services
    - `hooks/`: Custom React hooks
    - `types/`: TypeScript type definitions
    - `ui/features/`: Feature-specific UI components

## License

MIT 