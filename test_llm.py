# test_llm.py
from app.llm.provider import get_fast_llm, get_quality_llm

def test_fast_model():
    print("--- Testing Fast Model (Llama 1B) ---")
    llm = get_fast_llm()
    response = llm.invoke("Say 'Ollama connection successful' and nothing else.")
    print(f"Response: {response.content}\n")

def test_quality_model():
    print("--- Testing Quality Model (Qwen 14B) ---")
    llm = get_quality_llm()
    response = llm.invoke("Write one short sentence explaining why Python is great.")
    print(f"Response: {response.content}\n")

if __name__ == "__main__":
    test_fast_model()
    test_quality_model()