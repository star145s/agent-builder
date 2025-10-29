"""Authentication middleware and utilities for the miner API."""

import logging
from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from src.core.config import settings

logger = logging.getLogger(__name__)

# API Key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Verify the API key from the request header.
    API key is always required, even in development mode.
    
    Args:
        api_key: The API key from the X-API-Key header
        
    Returns:
        The verified API key
        
    Raises:
        HTTPException: If API key is missing or invalid
    """
    if api_key is None:
        logger.warning("Request missing API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Please provide X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    if api_key != settings.miner_api_key:
        logger.warning(f"Invalid API key attempted: {api_key[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
    
    return api_key


# Optional: For endpoints that don't require authentication
async def optional_api_key(api_key: str = Security(api_key_header)) -> bool:
    """
    Optional API key verification.
    
    Returns:
        True if API key is valid, False otherwise
    """
    if api_key is None:
        return False
    
    return api_key == settings.miner_api_key
