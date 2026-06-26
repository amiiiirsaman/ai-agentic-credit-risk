"""
Dynamic Confidence Calculator for Agent Results
Calculates confidence based on data quality, value ranges, and analysis success
"""
from typing import Dict, Any, Optional, List
import math


class ConfidenceCalculator:
    """
    Calculates dynamic confidence scores based on:
    - Data completeness (are all expected fields present?)
    - Value validity (are values within expected/reasonable ranges?)
    - Analysis quality (did LLM parsing succeed? Are outputs valid?)
    """
    
    @staticmethod
    def calculate_data_completeness(
        data: Dict[str, Any], 
        required_fields: List[str], 
        optional_fields: List[str] = None
    ) -> float:
        """
        Calculate completeness score (0-1) based on field presence
        Required fields weighted 2x vs optional fields
        """
        if not required_fields:
            return 0.8  # Default if no requirements specified
        
        optional_fields = optional_fields or []
        
        # Count present fields
        required_present = sum(1 for f in required_fields if _get_nested(data, f) is not None)
        optional_present = sum(1 for f in optional_fields if _get_nested(data, f) is not None)
        
        # Weighted score
        required_weight = 2.0
        optional_weight = 1.0
        
        total_weight = (len(required_fields) * required_weight + 
                       len(optional_fields) * optional_weight)
        
        achieved_weight = (required_present * required_weight + 
                          optional_present * optional_weight)
        
        return achieved_weight / total_weight if total_weight > 0 else 0.5
    
    @staticmethod
    def calculate_value_validity(
        data: Dict[str, Any],
        validation_rules: Dict[str, Dict[str, Any]]
    ) -> float:
        """
        Calculate validity score (0-1) based on whether values fall in expected ranges
        
        validation_rules format:
        {
            "field_path": {
                "min": 0,
                "max": 100,
                "expected_min": 20,  # Optimal range start
                "expected_max": 80,  # Optimal range end
            }
        }
        """
        if not validation_rules:
            return 0.85
        
        scores = []
        
        for field_path, rules in validation_rules.items():
            value = _get_nested(data, field_path)
            
            if value is None:
                scores.append(0.5)  # Missing data
                continue
            
            if not isinstance(value, (int, float)):
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    scores.append(0.5)
                    continue
            
            min_val = rules.get("min", float("-inf"))
            max_val = rules.get("max", float("inf"))
            expected_min = rules.get("expected_min", min_val)
            expected_max = rules.get("expected_max", max_val)
            
            # Check if in valid range at all
            if value < min_val or value > max_val:
                scores.append(0.3)  # Out of valid range - lower confidence
                continue
            
            # Check if in expected/optimal range
            if expected_min <= value <= expected_max:
                scores.append(1.0)  # In optimal range
            else:
                # Calculate distance from expected range
                if value < expected_min:
                    distance = (expected_min - value) / max(expected_min - min_val, 1)
                else:
                    distance = (value - expected_max) / max(max_val - expected_max, 1)
                
                scores.append(max(0.5, 1.0 - (distance * 0.3)))
        
        return sum(scores) / len(scores) if scores else 0.85
    
    @staticmethod
    def calculate_analysis_quality(
        llm_output: Dict[str, Any],
        expected_keys: List[str],
        has_reasoning: bool = False
    ) -> float:
        """
        Calculate analysis quality based on LLM output structure
        
        Args:
            llm_output: The parsed LLM response
            expected_keys: Keys that should be present in output
            has_reasoning: Whether reasoning was successfully extracted
        """
        if not llm_output:
            return 0.4  # LLM parsing failed
        
        # Check for expected keys
        keys_present = sum(1 for k in expected_keys if k in llm_output)
        key_score = keys_present / len(expected_keys) if expected_keys else 0.5
        
        # Bonus for having reasoning
        reasoning_bonus = 0.1 if has_reasoning else 0
        
        # Check if any values are error/fallback indicators
        error_indicators = ["error", "N/A", "unknown", "failed", "null"]
        error_count = 0
        for v in llm_output.values():
            if isinstance(v, str) and any(ind in v.lower() for ind in error_indicators):
                error_count += 1
        
        error_penalty = min(0.3, error_count * 0.05)
        
        return min(1.0, max(0.3, key_score + reasoning_bonus - error_penalty))
    
    @classmethod
    def calculate_overall_confidence(
        cls,
        data: Dict[str, Any],
        llm_output: Dict[str, Any],
        required_fields: List[str],
        optional_fields: List[str] = None,
        validation_rules: Dict[str, Dict[str, Any]] = None,
        expected_output_keys: List[str] = None,
        weights: Dict[str, float] = None
    ) -> float:
        """
        Calculate overall confidence score combining all factors
        
        Default weights:
        - Data completeness: 30%
        - Value validity: 30%
        - Analysis quality: 40%
        """
        weights = weights or {
            "completeness": 0.30,
            "validity": 0.30,
            "analysis": 0.40
        }
        
        completeness = cls.calculate_data_completeness(
            data, required_fields, optional_fields
        )
        
        validity = cls.calculate_value_validity(data, validation_rules or {})
        
        analysis = cls.calculate_analysis_quality(
            llm_output,
            expected_output_keys or [],
            has_reasoning=bool(llm_output.get("reasoning"))
        )
        
        overall = (
            completeness * weights.get("completeness", 0.3) +
            validity * weights.get("validity", 0.3) +
            analysis * weights.get("analysis", 0.4)
        )
        
        # Clamp to reasonable range and round
        return round(max(0.45, min(0.98, overall)), 4)


def _get_nested(data: Dict, path: str) -> Any:
    """Get nested value from dict using dot notation (e.g., 'credit.score')"""
    keys = path.split(".")
    current = data
    
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        else:
            return None
    
    return current


# Pre-defined validation rules for common fields
CREDIT_VALIDATION_RULES = {
    "credit.credit_score": {
        "min": 300, "max": 850,
        "expected_min": 580, "expected_max": 800
    },
    "credit.credit_utilization": {
        "min": 0, "max": 100,
        "expected_min": 0, "expected_max": 50
    },
    "credit.delinquencies_2yrs": {
        "min": 0, "max": 20,
        "expected_min": 0, "expected_max": 2
    },
    "credit.years_credit_history": {
        "min": 0, "max": 60,
        "expected_min": 3, "expected_max": 30
    }
}

INCOME_VALIDATION_RULES = {
    "employment.annual_income": {
        "min": 0, "max": 10000000,
        "expected_min": 30000, "expected_max": 500000
    },
    "employment.years_employed": {
        "min": 0, "max": 50,
        "expected_min": 2, "expected_max": 30
    }
}

LOAN_VALIDATION_RULES = {
    "loan.amount": {
        "min": 1000, "max": 10000000,
        "expected_min": 5000, "expected_max": 1000000
    },
    "loan.term_months": {
        "min": 6, "max": 480,
        "expected_min": 12, "expected_max": 360
    }
}
