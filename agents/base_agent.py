from langchain.llms import Ollama
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

class BaseAgent:
    def __init__(self, prompt=None, name=None, role=None):
        self.name = name or "Agent"
        self.role = role or "Generic Role"

        if prompt:
            self.prompt = PromptTemplate(
                input_variables=["event_name", "event_type", "location", "date", "description"],  
                template=prompt,
            )
            self.chain = LLMChain(llm=Ollama(model="phi3"), prompt=self.prompt)

    def run(self, inputs):
        if isinstance(inputs, dict):
            return self.chain.run(inputs)
        else:
            raise ValueError("Inputs must be a dictionary with required keys.")
