# test_classifier.py
from app.requirement_classifier import classify_requirement

def main():
    test_cases = [
        ("Must mention Jeremy", "deterministic"),
        ("Minimum 10 seconds", "deterministic"),
        ("Create curiosity", "semantic"),
        ("Positive portrayal of Jeremy", "semantic"),
        ("Maximum 50 words", "deterministic"),
        ("Must tag @jeremygreene", "deterministic"),
        ("Professional tone", "semantic"),
        ("Include the link https://whop.com", "deterministic")
    ]
    
    print("--- Testing Requirement Classifier ---")
    all_passed = True
    for desc, expected in test_cases:
        result = classify_requirement(desc)
        status = "✅" if result == expected else "❌"
        if result != expected:
            all_passed = False
        print(f"{status} '{desc}' -> {result} (Expected: {expected})")
        
    if all_passed:
        print("\nClassifier verified successfully!")

if __name__ == "__main__":
    main()