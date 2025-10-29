"""Utility functions for the miner API."""

import logging
from typing import Dict, Any


def setup_logging(log_level: str = "info") -> None:
    """
    Configure logging for the application.
    
    Args:
        log_level: Logging level (debug, info, warning, error)
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def format_error_response(error: Exception, detail: str = None) -> Dict[str, Any]:
    """
    Format an error into a standardized response.
    
    Args:
        error: The exception that occurred
        detail: Additional error details
        
    Returns:
        Dictionary with error information
    """
    return {
        "error": str(error),
        "detail": detail or type(error).__name__
    }


# Example function definitions for GPT-4o function calling
EXAMPLE_FUNCTIONS = [
    {
        "name": "get_current_weather",
        "description": "Get the current weather in a given location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA"
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "The temperature unit"
                }
            },
            "required": ["location"]
        }
    },
    {
        "name": "search_database",
        "description": "Search for information in a database",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results",
                    "default": 10
                }
            },
            "required": ["query"]
        }
    }
]
