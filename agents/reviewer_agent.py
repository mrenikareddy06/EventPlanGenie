from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.llms import Ollama

llm = Ollama(model="phi3")

prompt = """
You are a final event reviewer. Your job is to polish and validate the plan below.

Ensure:
- Section headers are formatted using Markdown (##, ###)
- Add emojis for each section (🎨, 📍, 🛍️, ⏰, 💌)
- Bullet points are clearly formatted
- Highlight any inconsistencies or improvements needed

Here is the plan:

{full_plan}

Respond with a complete and well-formatted version in Markdown.
"""

prompt_template = PromptTemplate(input_variables=["full_plan"], template=prompt)
chain = LLMChain(llm=llm, prompt=prompt_template)

def review_plan(full_plan: str) -> str:
    return chain.run({"full_plan": full_plan})
