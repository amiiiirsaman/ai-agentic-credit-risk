"""Unit tests for None safety in orchestrator and agents"""
import pytest


def test_operator_precedence_pattern():
    """Test the correct pattern for None-safe dict access"""
    # Simulating None result
    result = None
    
    # CORRECT pattern - the one we use now
    value = (result or {}).get("output") or {}
    assert value == {}
    
    # With actual result
    result = {"output": {"key": "value"}}
    value = (result or {}).get("output") or {}
    assert value == {"key": "value"}
    print("✓ Operator precedence pattern test passed")


def test_none_result_status_check():
    """Test status check with None result"""
    result = None
    
    # CORRECT pattern
    status = (result or {}).get("status")
    assert status is None
    
    # Check for failed status safely
    is_failed = (result or {}).get("status") == "failed"
    assert is_failed == False
    
    # With actual failed result
    result = {"status": "failed", "error": "Some error"}
    is_failed = (result or {}).get("status") == "failed"
    assert is_failed == True
    print("✓ None result status check test passed")


def test_nested_get_with_none():
    """Test nested .get() with None intermediate"""
    result = {"output": None}
    
    # CORRECT pattern with double safety
    output = (result or {}).get("output") or {}
    value = output.get("key", "default")
    assert value == "default"
    
    # With actual output
    result = {"output": {"key": "actual_value"}}
    output = (result or {}).get("output") or {}
    value = output.get("key", "default")
    assert value == "actual_value"
    print("✓ Nested get with None test passed")


def test_chief_output_extraction():
    """Test the chief_output extraction pattern used in orchestrator"""
    # Case 1: result is None
    result = None
    chief_output = (result or {}).get("output") or {}
    assert chief_output == {}
    assert chief_output.get("loan_terms", {}).get("conditions", []) == []
    
    # Case 2: result exists but output is None
    result = {"status": "failed", "output": None}
    chief_output = (result or {}).get("output") or {}
    assert chief_output == {}
    
    # Case 3: Normal result
    result = {"status": "completed", "output": {"decision": "APPROVE", "loan_terms": {"conditions": ["cond1"]}}}
    chief_output = (result or {}).get("output") or {}
    assert chief_output == {"decision": "APPROVE", "loan_terms": {"conditions": ["cond1"]}}
    assert chief_output.get("loan_terms", {}).get("conditions", []) == ["cond1"]
    print("✓ Chief output extraction test passed")


def test_explainability_output_extraction():
    """Test the explainability output extraction pattern"""
    # Case 1: result is None
    result = None
    exp_output = (result or {}).get("output") or {}
    assert exp_output.get("customer_explanation", "") == ""
    
    # Case 2: result exists but output is None
    result = {"status": "failed", "output": None}
    exp_output = (result or {}).get("output") or {}
    assert exp_output.get("customer_explanation", "") == ""
    
    # Case 3: Normal result
    result = {"status": "completed", "output": {"customer_explanation": "Your loan was approved!"}}
    exp_output = (result or {}).get("output") or {}
    assert exp_output.get("customer_explanation", "") == "Your loan was approved!"
    print("✓ Explainability output extraction test passed")


def test_state_decision_assignment():
    """Test the state decision assignment pattern"""
    result = None
    
    # CORRECT pattern
    decision = (result or {}).get("output") or {}
    assert decision == {}
    
    # With actual result
    result = {"output": {"decision": "APPROVE", "confidence_score": 0.95}}
    decision = (result or {}).get("output") or {}
    assert decision["decision"] == "APPROVE"
    assert decision["confidence_score"] == 0.95
    print("✓ State decision assignment test passed")


def run_all_tests():
    """Run all unit tests"""
    print("\n" + "="*60)
    print("RUNNING NONE SAFETY UNIT TESTS")
    print("="*60 + "\n")
    
    test_operator_precedence_pattern()
    test_none_result_status_check()
    test_nested_get_with_none()
    test_chief_output_extraction()
    test_explainability_output_extraction()
    test_state_decision_assignment()
    
    print("\n" + "="*60)
    print("ALL UNIT TESTS PASSED!")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_all_tests()
