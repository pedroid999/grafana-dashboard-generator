#!/usr/bin/env python
"""
Run the Grafana Dashboard Generator API.
"""

import os
import sys
import uvicorn
import dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("grafana-dashboard-generator")

# Load environment variables
dotenv.load_dotenv()

def main():
    """Run the API server."""
    logger.info("Starting Grafana Dashboard Generator API...")
    
    # Check if OpenAI API key is set
    if not os.environ.get("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEY environment variable is not set!")
        logger.warning("Set it in the .env file or export it in your shell.")
    
    # Run the FastAPI app with Uvicorn
    logger.info("Starting FastAPI server with Uvicorn on port 8000...")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload for development
        log_level="debug",
    )

if __name__ == "__main__":
    main() 