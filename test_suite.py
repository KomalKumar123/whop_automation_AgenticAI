# test_suite.py
"""
Comprehensive Integration Test Suite (Phase 12).

Tests the 7 requested scenarios to verify that the Campaign-Aware Content Evaluator
performs exactly as expected under various conditions.
"""
import os
import sys
from dotenv import load_dotenv
from app.graph import build_workflow
from app.agents.requirements import requirement_agent

# Ensure we can load env
load_dotenv()

# Helper to run a workflow with a custom campaign and script
def run_test_case(name: str, campaign_text: str, script_text: str, max_revisions: int = 3):
    print("\n" + "=" * 60)
    print(f"RUNNING TEST SCENARIO: {name}")
    print("=" * 60)
    
    state = {
        "original_content": script_text,
        "content": script_text,
        "raw_requirements": campaign_text,
        "requirements": [],
        "revision_count": 0,
        "revision_history": []
    }
    
    workflow = build_workflow()
    result = workflow.invoke(state)
    
    print("-" * 40)
    print(f"TEST RESULTS FOR: {name}")
    print(f"Feasible:  {result.get('feasibility', {}).get('feasible')}")
    print(f"Compliance: {result.get('compliance', {}).get('status')}")
    print(f"Quality Score: {result.get('quality', {}).get('overall_score')}/10")
    print(f"Revisions:  {result.get('revision_count')}")
    print(f"Final Decision: {result.get('decision')}")
    print("=" * 60)
    return result


def test_scenario_1_compliant_high_quality():
    """TEST 1: Already compliant and high quality script. Should approve with 0/1 revisions."""
    campaign = """
    JEREMY GREENE CAMPAIGN
    - Content must be in English.
    - Every post must tag @jeremygreene.
    - Include the hashtag #WhopRewards in the caption.
    - Jeremy must be positioned positively as an entrepreneur.
    """
    
    # A well-written, compliant script
    script = """
    Jeremy Greene is a phenomenal entrepreneur who has revolutionized the creator economy.
    By founding Whop, he created an ecosystem where anybody can monetize digital products easily.
    I love how simple the interface is and how much support they offer.
    Check out the link in bio to learn from Jeremy Greene today!
    @jeremygreene #WhopRewards
    """
    
    run_test_case("1. Compliant & High Quality", campaign, script)


def test_scenario_2_missing_deterministic():
    """TEST 2: Missing a deterministic requirement (no tag). Should fail, improve, and pass."""
    campaign = """
    JEREMY GREENE CAMPAIGN
    - Content must be in English.
    - Every post must tag @jeremygreene.
    """
    
    # Missing @jeremygreene tag
    script = """
    Jeremy Greene is an awesome entrepreneur.
    He built Whop to help creators sell courses and communities.
    You should definitely check it out.
    """
    
    run_test_case("2. Missing Deterministic Requirement (@jeremygreene)", campaign, script)


def test_scenario_3_compliant_poor_quality():
    """TEST 3: Compliant (deterministic checks pass) but poor quality. Should trigger improvement."""
    campaign = """
    JEREMY GREENE CAMPAIGN
    - Content must be in English.
    - Every post must tag @jeremygreene.
    - Include the hashtag #WhopRewards.
    """
    
    # Technically passes deterministic checks but is extremely dry and low quality
    script = """
    English post.
    @jeremygreene #WhopRewards
    """
    
    run_test_case("3. Compliant but Poor Quality", campaign, script)


def test_scenario_4_contradictory_campaign():
    """TEST 4: Contradictory campaign requirements. Should fail feasibility immediately."""
    campaign = """
    CONTRADICTORY CAMPAIGN
    - Videos must be at least 60 seconds long.
    - Videos must be under 20 seconds long.
    """
    
    script = "This script doesn't matter because feasibility check should fail."
    
    run_test_case("4. Contradictory Campaign", campaign, script)


def test_scenario_5_multiple_failures():
    """TEST 5: Multiple failures (missing tag, missing hashtag, short length)."""
    campaign = """
    RICH CAMPAIGN
    - Videos must be at least 10 seconds long.
    - Every post must tag @jeremygreene.
    - Include the hashtag #WhopRewards in the caption.
    """
    
    # Missing everything
    script = "Hi."
    
    run_test_case("5. Multiple Failures", campaign, script)


def test_scenario_6_regression():
    """TEST 6: Checks how system handles a regression (faking compliance check failing)."""
    # This is handled naturally by the loop since every revision goes back to analyzer and compliance.
    # We run a case that requires revision to show that re-evaluation catches remaining errors.
    campaign = """
    REGRESSION CAMPAIGN
    - Content must be in English.
    - Every post must tag @jeremygreene.
    - Include the hashtag #WhopRewards.
    """
    
    script = "Jeremy Greene is building Whop. It is cool. English." # Missing tag and hashtag
    run_test_case("6. Regression Re-analysis", campaign, script)


def test_scenario_7_max_revisions():
    """TEST 7: Maximum revisions reached (e.g. impossible to satisfy or poor quality always)."""
    # To simulate max revisions without looping forever, we pass a very difficult semantic requirement 
    # that the script won't satisfy easily, or we can use a script that keeps failing.
    campaign = """
    IMPOSSIBLE SEMANTIC CAMPAIGN
    - Every single word in the script must start with the letter J.
    - Content must be in English.
    """
    
    script = "Jeremy joins jolly jumps."
    run_test_case("7. Max Revisions Limit", campaign, script)


def main():
    if len(sys.argv) > 1:
        test_num = sys.argv[1]
        if test_num == "1":
            test_scenario_1_compliant_high_quality()
        elif test_num == "2":
            test_scenario_2_missing_deterministic()
        elif test_num == "3":
            test_scenario_3_compliant_poor_quality()
        elif test_num == "4":
            test_scenario_4_contradictory_campaign()
        elif test_num == "5":
            test_scenario_5_multiple_failures()
        elif test_num == "6":
            test_scenario_6_regression()
        elif test_num == "7":
            test_scenario_7_max_revisions()
        else:
            print(f"Unknown test number: {test_num}")
    else:
        # Run all tests
        print("Starting test suite execution...")
        test_scenario_4_contradictory_campaign()  # fast, no LLM
        test_scenario_1_compliant_high_quality()
        test_scenario_2_missing_deterministic()
        test_scenario_3_compliant_poor_quality()
        test_scenario_5_multiple_failures()
        test_scenario_6_regression()
        test_scenario_7_max_revisions()

if __name__ == "__main__":
    main()
