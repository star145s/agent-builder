"""LLM API client wrapper with support for OpenAI and vLLM.

This module provides a unified interface for interacting with Large Language Models
through different providers:
- OpenAI: Cloud-based API (GPT-4o, GPT-4-turbo, etc.)
- vLLM: Self-hosted models (Llama, Qwen, Mistral, etc.)

The client automatically detects the provider from settings and provides
an OpenAI-compatible interface for both.
"""

import logging
from typing import Optional, List, Dict, Any
from openai import AsyncOpenAI, OpenAIError
import httpx
from src.core.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Unified wrapper for LLM APIs (OpenAI and vLLM-compatible endpoints)."""
    
    def __init__(self):
        """Initialize the LLM client based on configured provider."""
        self.provider = settings.llm_provider.lower()
        self.model = settings.get_model_name
        
        # Configure HTTP client with connection pooling for better performance
        http_client = httpx.AsyncClient(
            limits=httpx.Limits(
                max_keepalive_connections=settings.connection_pool_keepalive,
                max_connections=settings.connection_pool_max,
                keepalive_expiry=float(settings.connection_pool_keepalive_expiry)
            ),
            timeout=httpx.Timeout(
                connect=10.0,   # 10s to establish connection
                read=float(settings.request_timeout),
                write=10.0,     # 10s to write request
                pool=5.0        # 5s to get connection from pool
            )
        )
        
        if self.provider == "openai":
            # Standard OpenAI configuration with connection pooling
            self.client = AsyncOpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                http_client=http_client
            )
            logger.info(f"Initialized OpenAI client with model: {self.model} (with connection pooling)")
        
        elif self.provider == "vllm":
            # vLLM uses OpenAI-compatible API with connection pooling
            self.client = AsyncOpenAI(
                api_key=settings.vllm_api_key,
                base_url=settings.get_vllm_base_url,
                http_client=http_client
            )
            logger.info(f"Initialized vLLM client at {settings.get_vllm_base_url} with model: {self.model} (with connection pooling)")
        
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}. Use 'openai' or 'vllm'.")
    
    async def generate_response(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None,
        response_format: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Generate a response using GPT-4o.
        
        Args:
            prompt: The input prompt
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            conversation_history: Previous conversation messages
            system_prompt: Optional system prompt to guide behavior
            response_format: Optional response format (e.g., {"type": "json_object"})
            
        Returns:
            Dictionary containing response and metadata
            
        Raises:
            OpenAIError: If the API call fails
        """
        try:
            # Prepare messages
            messages = []
            
            # Add system prompt if provided (must be first)
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            # Add conversation history if provided (filter out null/empty messages)
            if conversation_history:
                for i, msg in enumerate(conversation_history):
                    content = msg.get("content")
                    # Skip messages with null, empty, or non-string content
                    if content is None:
                        logger.warning(f"Skipping message {i} with null content")
                        continue
                    if not isinstance(content, str):
                        logger.warning(f"Skipping message {i} with non-string content: {type(content)}")
                        continue
                    if not content.strip():
                        logger.warning(f"Skipping message {i} with empty content")
                        continue
                    
                    # Add valid message
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": content
                    })
            
            # Add current prompt (skip if empty)
            if prompt and prompt.strip():
                messages.append({"role": "user", "content": prompt})
            
            logger.info(f"Prepared {len(messages)} messages for OpenAI API")
            
            # Prepare API parameters
            params = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens or settings.max_tokens,
                "temperature": temperature if temperature is not None else settings.temperature
            }
            
            # Add response format if provided (for JSON mode)
            if response_format:
                params["response_format"] = response_format
            
            # Make API call
            logger.info(f"Calling OpenAI API with model: {self.model}")
            response = await self.client.chat.completions.create(**params)
            
            # Extract response data
            message = response.choices[0].message
            
            result = {
                "response": message.content or "",
                "model": response.model,
                "tokens_used": response.usage.total_tokens,
                "finish_reason": response.choices[0].finish_reason
            }
            
            logger.info(f"Successfully generated response. Tokens used: {result['tokens_used']}")
            return result
            
        except OpenAIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in generate_response: {str(e)}")
            raise
    
    async def complete_text(
        self,
        text_to_complete: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Complete/continue text using chat completion API (simulates text completion).
        
        This simulates the old completion API by using the chat API with the text
        as an assistant message prefix, prompting the model to continue naturally.
        
        Args:
            text_to_complete: The text prefix to continue from
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            system_prompt: Optional system prompt
            
        Returns:
            Dictionary containing completion and metadata
            
        Raises:
            OpenAIError: If the API call fails
        """
        try:
            # Prepare messages for text continuation
            messages = []
            
            # Add system prompt if provided
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            # Add the text as an assistant message (to continue from)
            # This tricks the model into continuing the text naturally
            messages.append({"role": "assistant", "content": text_to_complete})
            
            # Add a user message prompting continuation
            messages.append({"role": "user", "content": "Continue."})
            
            logger.info(f"Completing text (length: {len(text_to_complete)} chars)")
            
            # Prepare API parameters
            params = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens or settings.max_tokens,
                "temperature": temperature if temperature is not None else settings.temperature
            }
            
            # Make API call
            response = await self.client.chat.completions.create(**params)
            
            # Extract response data
            message = response.choices[0].message
            
            result = {
                "completion": message.content or "",
                "model": response.model,
                "tokens_used": response.usage.total_tokens,
                "finish_reason": response.choices[0].finish_reason
            }
            
            logger.info(f"Successfully completed text. Tokens used: {result['tokens_used']}")
            return result
            
        except OpenAIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in complete_text: {str(e)}")
            raise
    
    async def generate_streaming_response(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ):
        """
        Generate a streaming response using GPT-4o.
        
        Args:
            prompt: The input prompt
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            
        Yields:
            Response chunks as they arrive
        """
        try:
            params = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens or settings.max_tokens,
                "temperature": temperature if temperature is not None else settings.temperature,
                "stream": True
            }
            
            logger.info(f"Starting streaming response with model: {self.model}")
            
            async for chunk in await self.client.chat.completions.create(**params):
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except OpenAIError as e:
            logger.error(f"OpenAI streaming error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in streaming: {str(e)}")
            raise
    
    async def check_health(self) -> bool:
        """
        Check if the OpenAI API is accessible.
        
        Returns:
            True if API is accessible, False otherwise
        """
        try:
            # Simple test call
            await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            return True
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False


# Global client instance
llm_client = LLMClient()


def get_llm_client() -> LLMClient:
    """Get the global LLM client instance."""
    return llm_client


# Convenience function for easier imports
async def generate_response(
    prompt: str,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    system_prompt: Optional[str] = None,
    user_message: Optional[str] = None,
    response_format: Optional[Dict[str, str]] = None
) -> str:
    """
    Convenience function to generate a response using the global client.
    
    Args:
        prompt: The input prompt (used if user_message not provided)
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature
        conversation_history: Previous conversation messages
        system_prompt: Optional system prompt to guide behavior
        user_message: Optional user message (overrides prompt if provided)
        response_format: Optional response format (e.g., {"type": "json_object"})
        
    Returns:
        The generated response text
    """
    result = await llm_client.generate_response(
        prompt=user_message if user_message else prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        conversation_history=conversation_history,
        system_prompt=system_prompt,
        response_format=response_format
    )
    return result["response"]


async def complete_text(
    text_to_complete: str,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    system_prompt: Optional[str] = None
) -> str:
    """
    Convenience function to complete/continue text using the global client.
    
    Args:
        text_to_complete: The text prefix to continue from
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature
        system_prompt: Optional system prompt
        
    Returns:
        The completed/continued text
    """
    result = await llm_client.complete_text(
        text_to_complete=text_to_complete,
        max_tokens=max_tokens,
        temperature=temperature,
        system_prompt=system_prompt
    )
    return result["completion"]
