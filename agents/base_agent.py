import logging
from typing import Any, Dict, Optional, Union
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_core.language_models import BaseLanguageModel

logger = logging.getLogger(__name__)

class BaseAgent:
    def __init__(
        self,
        prompt: Union[str, PromptTemplate] = None,
        name: str = "Agent",
        role: str = "Generic Agent",
        model: str = "phi3",
        temperature: float = 0.7,
        llm: Optional[BaseLanguageModel] = None  # ✅ Accept external LLM
    ):
        self.name = name
        self.role = role
        self.model = model
        self.temperature = temperature

        # ✅ Use provided LLM if available (shared), else create new one
        self.llm = llm or Ollama(model=model, temperature=temperature)

        self.chain = None
        if prompt:
            if isinstance(prompt, str):
                self.prompt = PromptTemplate.from_template(prompt)
            else:
                self.prompt = prompt
            self.chain = LLMChain(llm=self.llm, prompt=self.prompt)

    def run(self, inputs: Dict[str, Any]) -> str:
        """Run the agent with processed inputs"""
        if not self.chain:
            raise ValueError(f"{self.name} is not configured with a prompt.")
        try:
            processed_inputs = self._process_inputs(inputs)
            output = self.chain.run(processed_inputs).strip()
            if not output:
                logger.warning(f"{self.name} returned empty output.")
                return self.fallback_output(processed_inputs)
            return output
        except Exception as e:
            logger.error(f"Error running {self.name}: {str(e)}")
            return self.fallback_output(inputs)

    def _process_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and standardize input values"""
        processed = inputs.copy()
        if "price_range" in processed and isinstance(processed["price_range"], (tuple, list)):
            processed["price_range_0"] = processed["price_range"][0]
            processed["price_range_1"] = processed["price_range"][1]
        for k, v in processed.items():
            if isinstance(v, str):
                processed[k] = v.strip()
            elif v is None:
                processed[k] = "Not specified"
        return processed

    def fallback_output(self, inputs: Dict[str, Any]) -> str:
        """Default fallback logic when LLM fails"""
        return f"⚠️ {self.name} was unable to generate a valid response. Please refine inputs or try again."
