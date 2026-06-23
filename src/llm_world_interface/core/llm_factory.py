from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel


class LLMFactory:
    """Factory to initialize LLM instances based on the requested provider."""

    @staticmethod
    def get_llm(provider: str, model_name: str, **kwargs: Any) -> BaseChatModel:
        if provider.lower() == "gemini":
            # Requires `pip install langchain-google-genai` and GEMINI_API_KEY
            from langchain_google_genai import ChatGoogleGenerativeAI

            return ChatGoogleGenerativeAI(model=model_name, **kwargs)

        elif provider.lower() == "openai":
            # Requires `pip install langchain-openai` and OPENAI_API_KEY
            from langchain_openai import ChatOpenAI

            return ChatOpenAI(model=model_name, **kwargs)

        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
