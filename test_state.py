from app.state import ContentState


def main():
    state: ContentState = {
        "original_content": "Jeremy talks about his business.",
        "content": "Jeremy talks about his business.",
        "raw_requirements": "Mention Jeremy and create curiosity.",
        "revision_count": 0,
        "revision_history": []
    }

    print("State created successfully.")
    print("Content:", state["content"])
    print("Revision:", state["revision_count"])


if __name__ == "__main__":
    main()