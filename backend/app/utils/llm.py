"""
LLM utilities and provider configuration.
"""

import os
import logging
from typing import Any, Dict, List, Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from app.schemas.models import ModelProvider

logger = logging.getLogger(__name__)

def get_llm(provider: ModelProvider, **kwargs: Any) -> BaseChatModel:
    """
    Get the LLM instance for the specified provider.
    
    Args:
        provider: The LLM provider to use
        **kwargs: Additional keyword arguments to pass to the LLM constructor
        
    Returns:
        An instance of the requested LLM
        
    Raises:
        ValueError: If the requested provider is not supported
    """
    temperature = kwargs.get("temperature", 0.1)  # Low temperature for JSON generation
    
    try:
        if provider == ModelProvider.OPENAI:
            return ChatOpenAI(
                model="gpt-4-0125-preview",  # Using a known available model
                temperature=temperature,
            )
        elif provider == ModelProvider.OPENAI4O:
            # For optimized version, using GPT-4 Turbo with specific settings
            return ChatOpenAI(
                model="gpt-4-0125-preview",  # Using a known available model
                temperature=temperature,
                max_tokens=4096,  # Ensure enough context for JSON generation
                top_p=0.1,  # More focused sampling
                presence_penalty=0.0,
                frequency_penalty=0.0,
            )
        elif provider == ModelProvider.ANTHROPIC:
            return ChatAnthropic(
                model="claude-3-opus-20240229",
                temperature=temperature,
            )
        else:
            raise ValueError(f"Unsupported model provider: {provider}")
    except Exception as e:
        logger.error(f"Error initializing LLM for provider {provider}: {str(e)}")
        # Fallback to GPT-4 if available
        logger.info("Attempting to fallback to GPT-4...")
        return ChatOpenAI(
            model="gpt-4",
            temperature=temperature,
        )


# System prompts for different tasks
DASHBOARD_GENERATION_SYSTEM_PROMPT = """You are an expert in creating Grafana dashboards. 
Your task is to generate a valid JSON configuration for a Grafana dashboard based on the user's description.

The generated JSON should follow these guidelines:
1. Include all required fields: panels, title
2. Each panel should have id, type, title, and proper gridPos
3. Use appropriate data sources and query expressions
4. Include reasonable visualization options
5. Ensure the dashboard is well-organized and visually effective

IMPORTANT: You must output ONLY the valid JSON object with no additional text or explanations.

Example of a valid panel structure:
{
  "id": 1,
  "type": "graph",
  "title": "Panel Title",
  "gridPos": {
    "h": 8,
    "w": 12,
    "x": 0,
    "y": 0
  }
}
"""

DASHBOARD_FIX_SYSTEM_PROMPT = """You are an expert in fixing Grafana dashboard JSON configurations.
You will be given a JSON configuration that has validation errors, along with error descriptions.

Your task is to fix these errors and return the corrected JSON configuration.

IMPORTANT:
1. Fix all validation errors
2. Only output the fixed JSON with no additional text or explanation
3. Ensure all required fields are present and have the correct types
4. Maintain as much of the original structure and intent as possible

Example of a valid panel structure:
{
  "id": 1,
  "type": "graph",
  "title": "Panel Title",
  "gridPos": {
    "h": 8,
    "w": 12,
    "x": 0,
    "y": 0
  }
}
"""

RAG_AUGMENTED_PROMPT = """I am generating a Grafana dashboard for the following description:

{user_prompt}

I have some additional context that might be helpful:

{rag_context}

Please generate a complete, valid JSON configuration for a Grafana dashboard based on this information. 
Make sure to include all required fields and properties according to the Grafana dashboard schema.

The JSON must include:
1. A dashboard title
2. At least one panel with proper configuration
3. Valid gridPos for each panel
4. Appropriate data source and query configuration
"""


def create_dashboard_generator_chain(llm: BaseChatModel) -> Any:
    """
    Create a chain for generating dashboard JSON.
    
    Args:
        llm: The LLM to use for generation
        
    Returns:
        A chain that generates dashboard JSON
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=DASHBOARD_GENERATION_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{prompt}"),
        ]
    )
    
    return prompt | llm


def create_dashboard_fix_chain(llm: BaseChatModel) -> Any:
    """
    Create a chain for fixing dashboard JSON based on validation errors.
    
    Args:
        llm: The LLM to use for fixing
        
    Returns:
        A chain that fixes dashboard JSON
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=DASHBOARD_FIX_SYSTEM_PROMPT),
            ("human", """
Here's a Grafana dashboard JSON with validation errors:

{dashboard_json}

The following errors were found:
{error_patterns}

Please provide the fixed JSON that resolves these errors.
"""),
        ]
    )
    
    return prompt | llm 