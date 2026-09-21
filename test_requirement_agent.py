# test_requirement_agent.py
from app.agents.requirements import requirement_agent

def main():
    print("=== Testing Requirement Agent (Rich Campaign) ===\n")

    # 1. Read the campaign file
    with open("data/campaign.txt", "r") as f:
        campaign_text = f.read()

    # 2. Setup initial state
    initial_state = {
        "raw_requirements": campaign_text,
        "revision_count": 0,
        "revision_history": []
    }

    # 3. Run the agent
    result = requirement_agent(initial_state)

    # 4. Print the structured output
    print(f"\n--- EXTRACTED REQUIREMENTS ({len(result['requirements'])}) ---")
    for i, req in enumerate(result["requirements"], 1):
        cond = f" [IF: {req['condition']}]" if req.get("condition") else ""
        print(f"\n{i}. {req['description']}")
        print(f"   Rule:      {req['rule']}")
        print(f"   Type:      {req['type']}")
        print(f"   Scope:     {req['scope']}")
        if cond:
            print(f"   Condition: {req['condition']}")

    # 5. Summary statistics
    types = {}
    scopes = {}
    conditional = 0
    for req in result["requirements"]:
        types[req["type"]] = types.get(req["type"], 0) + 1
        scopes[req["scope"]] = scopes.get(req["scope"], 0) + 1
        if req.get("condition"):
            conditional += 1

    print(f"\n--- SUMMARY ---")
    print(f"Total: {len(result['requirements'])}")
    print(f"Types: {types}")
    print(f"Scopes: {scopes}")
    print(f"Conditional: {conditional}")

if __name__ == "__main__":
    main()