# test_structured_output.py
from pydantic import BaseModel, Field
from typing import Literal
from app.llm.provider import get_fast_llm

# 1. Define the Pydantic schema we want the LLM to return
class Requirement(BaseModel):
    rule: str = Field(description="The specific constraint, e.g., 'max_words' or 'tone'")
    type: Literal["deterministic", "semantic"]
    description: str = Field(description="The original text of the requirement")

class RequirementList(BaseModel):
    requirements: list[Requirement]

def main():
    print("--- Testing Llama 1B Structured Output ---")
    llm = get_fast_llm()
    
    # Bind the Pydantic schema to the LLM
    structured_llm = llm.with_structured_output(RequirementList)
    
    # Give it a small, controlled input
    prompt = """
    Extract the requirements from the following text:
    - Must mention Jeremy
    - Minimum 10 seconds
    - Create curiosity
    """
    
    print("Invoking LLM...")
    result = structured_llm.invoke(prompt)
    
    print("\n--- Raw Pydantic Object ---")
    print(result)
    
    print("\n--- Formatted Output ---")
    for req in result.requirements:
        print(f"Rule: {req.rule} | Type: {req.type} | Desc: {req.description}")

if __name__ == "__main__":
    main()