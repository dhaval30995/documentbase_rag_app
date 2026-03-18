"""
LLM service.
Connects to the Groq API and generates text responses
using the specified language model.
"""

import logging

from groq import Groq

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class LLMService:
    """
    Manages communication with the Groq API for text generation.
    Uses the gpt-oss-120b model by default.
    """

    _instance: "LLMService | None" = None
    _client: Groq | None = None

    def __new__(cls) -> "LLMService":
        """Singleton pattern — one Groq client per process."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if LLMService._client is None:
            settings = get_settings()
            if not settings.GROQ_API_KEY:
                logger.error("GROQ_API_KEY is not configured")
                raise ValueError("GROQ_API_KEY must be set in environment variables")

            LLMService._client = Groq(api_key=settings.GROQ_API_KEY)
            self._model_name = settings.LLM_MODEL_NAME
            logger.info("Groq LLM client initialized with model: %s", self._model_name)

    def generate_response(
        self,
        prompt: str,
        system_prompt: str = "You are a helpful assistant that answers questions based on the provided context. If the context doesn't contain relevant information, say so honestly.",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """
        Generate a text response from the LLM.

        Args:
            prompt: The user prompt (including context).
            system_prompt: System-level instructions for the model.
            temperature: Sampling temperature (0.0–2.0).
            max_tokens: Maximum tokens in the response.

        Returns:
            The generated text response.
        """
        try:
            settings = get_settings()
            chat_completion = self._client.chat.completions.create(
                model=settings.LLM_MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )

            response_text = chat_completion.choices[0].message.content
            logger.info("LLM generated response (%d chars)", len(response_text))
            return response_text

        except Exception as e:
            logger.error("LLM generation failed: %s", str(e))
            raise RuntimeError(f"Failed to generate LLM response: {str(e)}") from e

    def generate_response_stream(
        self,
        prompt: str,
        system_prompt: str = "You are a helpful assistant that answers questions based on the provided context. If the context doesn't contain relevant information, say so honestly.",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ):
        """
        Generate a text response from the LLM, streaming the output.

        Args:
            prompt: The user prompt (including context).
            system_prompt: System-level instructions for the model.
            temperature: Sampling temperature (0.0–2.0).
            max_tokens: Maximum tokens in the response.

        Yields:
            Chunks of the generated text response.
        """
        try:
            settings = get_settings()
            stream = self._client.chat.completions.create(
                model=settings.LLM_MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error("LLM streaming generation failed: %s", str(e))
            raise RuntimeError(f"Failed to stream LLM response: {str(e)}") from e
