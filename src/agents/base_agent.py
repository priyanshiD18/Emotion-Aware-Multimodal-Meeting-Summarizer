"""
Base agent class for all LangChain agents
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
import logging

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all agents in the system"""
    
    def __init__(
        self,
        llm_provider: str = "openai",
        model_name: str = "gpt-4-turbo-preview",
        temperature: float = 0.3,
        api_key: Optional[str] = None
    ):
        """
        Initialize base agent
        
        Args:
            llm_provider: LLM provider ("openai" or "google")
            model_name: Model identifier
            temperature: Sampling temperature
            api_key: API key for the provider
        """
        self.llm_provider = llm_provider
        self.model_name = model_name
        self.temperature = temperature
        self.api_key = api_key
        
        self.llm = self._initialize_llm()
        self.prompt_template = self._create_prompt_template()
        
        logger.info(
            f"Initialized {self.__class__.__name__}: "
            f"provider={llm_provider}, model={model_name}"
        )
    
    def _initialize_llm(self):
        """Initialize the LLM based on provider"""
        if self.llm_provider == "openai":
            return ChatOpenAI(
                model_name=self.model_name,
                temperature=self.temperature,
                api_key=self.api_key
            )
        elif self.llm_provider == "google":
            return ChatGoogleGenerativeAI(
                model=self.model_name,
                temperature=self.temperature,
                google_api_key=self.api_key
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")
    
    @abstractmethod
    def _create_prompt_template(self) -> PromptTemplate:
        """Create the prompt template for this agent"""
        pass
    
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input and return results
        
        Args:
            input_data: Input data for the agent
            
        Returns:
            Processed results
        """
        pass
    
    def format_prompt(self, **kwargs) -> str:
        """Format the prompt with provided kwargs"""
        return self.prompt_template.format(**kwargs)
    
    def invoke_llm(self, prompt: str) -> str:
        """
        Invoke the LLM with a prompt
        
        Args:
            prompt: Formatted prompt
            
        Returns:
            LLM response
        """
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            logger.error(f"LLM invocation failed: {e}")
            raise

