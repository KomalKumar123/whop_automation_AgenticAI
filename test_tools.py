# test_tools.py
from app.tools import count_words, check_keyword

def main():
    text = "Jeremy is building an amazing AI automation platform."
    
    # Test 1: Word count
    word_count = count_words.invoke({"text": text})
    print(f"Word count test: {word_count} (Expected: 8)")
    
    # Test 2: Keyword found
    keyword_result = check_keyword.invoke({"text": text, "keyword": "Jeremy"})
    print(f"Keyword 'Jeremy' found: {keyword_result['found']}")
    print(f"Evidence: {keyword_result['evidence']}")
    
    # Test 3: Keyword missing
    missing_result = check_keyword.invoke({"text": text, "keyword": "Python"})
    print(f"Keyword 'Python' found: {missing_result['found']}")

if __name__ == "__main__":
    main()