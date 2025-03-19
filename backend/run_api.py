#!/usr/bin/env python
"""
Run the Grafana Dashboard Generator API.
"""

import os
import sys
import uvicorn
import dotenv

# Load environment variables
dotenv.load_dotenv()

def main():
    """Run the API server."""
    print("Starting Grafana Dashboard Generator API...")
    
    # Check if OpenAI API key is set
    if not os.environ.get("OPENAI_API_KEY"):
        print("WARNING: OPENAI_API_KEY environment variable is not set!")
        print("Set it in the .env file or export it in your shell.")
    
    # Run the FastAPI app with Uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload for development
    )

if __name__ == "__main__":
    main() 