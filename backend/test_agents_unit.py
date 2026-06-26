"""
Unit Tests for All 11 Credit Risk Assessment Agents
====================================================
30 tests covering: ConfidenceCalculator, QuantitativeRisk, FraudDetection,
IncomeVerification, CreditHistory, ChiefUnderwriter, Compliance, Collateral,
DocumentIntelligence, MarketConditions, Explainability

These tests use the ACTUAL agent calculation methods (non-LLM) to test logic independently.
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any

# Import agents
from agents.document_intelligence_agent import DocumentIntelligenceAgent
from agents.fraud_detection_agent import FraudDetectionAgent
from agents.income_verification_agent import IncomeVerificationAgent
from agents.credit_history_agent import CreditHistoryAgent
from agents.quantitative_risk_agent import QuantitativeRiskAgent
from agents.collateral_agent import CollateralAgent
from agents.customer_relationship_agent import CustomerRelationshipAgent
from agents.market_conditions_agent import MarketConditionsAgent
from agents.compliance_agent import ComplianceAgent
from agents.chief_underwriter_agent import ChiefUnderwriterAgent
from agents.explainability_agent import ExplainabilityAgent
from agents.confidence_calculator import ConfidenceCalculator, CREDIT_VALIDATION_RULES
from synthetic_data import SyntheticDataGenerator


# =============================================================================
# TEST DATA FIXTURES
# =============================================================================

def get_low_risk_application() -> Dict[str, Any]:
    """Generate a LOW_RISK test application"""
    return SyntheticDataGenerator.generate_application("low_risk")

def get_medium_risk_application() -> Dict[str, Any]:
    """Generate a MEDIUM_RISK test application"""
    return SyntheticDataGenerator.generate_application("medium_risk")

def get_high_risk_application() -> Dict[str, Any]:
    """Generate a HIGH_RISK test application"""
    return SyntheticDataGenerator.generate_application("high_risk")

def get_mock_agent_results(risk_level: str = "low") -> Dict[str, Any]:
    """Create mock agent results for testing ChiefUnderwriter"""
    if risk_level == "low":
        return {
            "DocumentIntelligence": {"confidence": 0.95, "output": {"verification_status": "verified"}},
            "FraudDetection": {"confidence": 0.92, "output": {"fraud_risk_score": 0.05}},
            "IncomeVerification": {"confidence": 0.90, "output": {"income_verified": True, "dti_ratio": 0.20}},
            "CreditHistory": {"confidence": 0.93, "output": {"credit_quality": "excellent"}},
            "QuantitativeRisk": {"confidence": 0.91, "output": {"default_probability": 0.03, "risk_level": "Low"}},
            "Collateral": {"confidence": 0.88, "output": {"ltv_ratio": 0.70}},
            "CustomerRelationship": {"confidence": 0.85, "output": {"customer_value": "high"}},
            "MarketConditions": {"confidence": 0.87, "output": {"market_risk": "low"}},
            "Compliance": {"confidence": 0.95, "output": {"compliant": True}},
        }
    elif risk_level == "high":
        return {
            "DocumentIntelligence": {"confidence": 0.70, "output": {"verification_status": "partial"}},
            "FraudDetection": {"confidence": 0.65, "output": {"fraud_risk_score": 0.45}},
            "IncomeVerification": {"confidence": 0.60, "output": {"income_verified": False, "dti_ratio": 0.65}},
            "CreditHistory": {"confidence": 0.55, "output": {"credit_quality": "poor"}},
            "QuantitativeRisk": {"confidence": 0.70, "output": {"default_probability": 0.55, "risk_level": "Critical"}},
            "Collateral": {"confidence": 0.60, "output": {"ltv_ratio": 0.95}},
            "CustomerRelationship": {"confidence": 0.50, "output": {"customer_value": "low"}},
            "MarketConditions": {"confidence": 0.65, "output": {"market_risk": "high"}},
            "Compliance": {"confidence": 0.75, "output": {"compliant": True}},
        }
    else:  # medium
        return {
            "DocumentIntelligence": {"confidence": 0.85, "output": {"verification_status": "verified"}},
            "FraudDetection": {"confidence": 0.80, "output": {"fraud_risk_score": 0.15}},
            "IncomeVerification": {"confidence": 0.78, "output": {"income_verified": True, "dti_ratio": 0.38}},
            "CreditHistory": {"confidence": 0.75, "output": {"credit_quality": "fair"}},
            "QuantitativeRisk": {"confidence": 0.77, "output": {"default_probability": 0.20, "risk_level": "Medium"}},
            "Collateral": {"confidence": 0.72, "output": {"ltv_ratio": 0.85}},
            "CustomerRelationship": {"confidence": 0.70, "output": {"customer_value": "medium"}},
            "MarketConditions": {"confidence": 0.75, "output": {"market_risk": "moderate"}},
            "Compliance": {"confidence": 0.85, "output": {"compliant": True}},
        }


# =============================================================================
# TEST 1-3: CONFIDENCE CALCULATOR TESTS
# =============================================================================

class TestConfidenceCalculator(unittest.TestCase):
    """Tests for the ConfidenceCalculator utility"""
    
    def test_1_data_completeness_full_data(self):
        """Test 1: Data completeness with all required fields present"""
        application = get_low_risk_application()
        required_fields = ["applicant.name", "credit.credit_score", "employment.annual_income"]
        optional_fields = ["financial.savings_balance"]
        
        score = ConfidenceCalculator.calculate_data_completeness(
            application, required_fields, optional_fields
        )
        
        self.assertGreaterEqual(score, 0.8, "Full data should have high completeness score")
        self.assertLessEqual(score, 1.0)
        print(f"  Test 1 PASSED: Data completeness = {score:.2%}")
    
    def test_2_value_validity_low_risk(self):
        """Test 2: Value validity scoring for low-risk application"""
        application = get_low_risk_application()
        
        # Use the actual CREDIT_VALIDATION_RULES format
        score = ConfidenceCalculator.calculate_value_validity(application, CREDIT_VALIDATION_RULES)
        
        self.assertGreaterEqual(score, 0.5, "Low-risk app should have reasonable validity")
        self.assertLessEqual(score, 1.0)
        print(f"  Test 2 PASSED: Value validity = {score:.2%}")
    
    def test_3_analysis_quality_scoring(self):
        """Test 3: Analysis quality scoring with LLM output"""
        llm_output = {
            "decision": "APPROVE",
            "confidence_score": 0.92,
            "risk_level": "Low",
            "reasoning": "Strong credit profile with stable income"
        }
        required_keys = ["decision", "confidence_score", "risk_level"]
        
        score = ConfidenceCalculator.calculate_analysis_quality(llm_output, required_keys)
        
        self.assertGreaterEqual(score, 0.9, "Complete LLM output should have high quality score")
        print(f"  Test 3 PASSED: Analysis quality = {score:.2%}")


# =============================================================================
# TEST 4-7: QUANTITATIVE RISK AGENT TESTS
# =============================================================================

class TestQuantitativeRiskAgent(unittest.TestCase):
    """Tests for the QuantitativeRiskAgent"""
    
    def setUp(self):
        self.agent = QuantitativeRiskAgent()
    
    def test_4_feature_extraction(self):
        """Test 4: Feature extraction from application data"""
        application = get_low_risk_application()
        features = self.agent._extract_features(application)
        
        self.assertIn("credit_score", features)
        self.assertIn("dti_ratio", features)
        self.assertIn("loan_to_income", features)  # Not annual_income directly
        self.assertGreaterEqual(features["credit_score"], 300)
        self.assertLessEqual(features["credit_score"], 850)
        print(f"  Test 4 PASSED: Extracted {len(features)} features, credit_score={features['credit_score']}")
    
    def test_5_default_probability_low_risk(self):
        """Test 5: Default probability calculation for low-risk applicant"""
        application = get_low_risk_application()
        features = self.agent._extract_features(application)
        
        default_prob = self.agent._calculate_default_probability(features)
        
        self.assertLess(default_prob, 0.20, "Low-risk should have <20% default probability")
        print(f"  Test 5 PASSED: Low-risk default probability = {default_prob:.2%}")
    
    def test_6_default_probability_high_risk(self):
        """Test 6: Default probability calculation for high-risk applicant"""
        application = get_high_risk_application()
        features = self.agent._extract_features(application)
        
        default_prob = self.agent._calculate_default_probability(features)
        
        self.assertGreater(default_prob, 0.30, "High-risk should have >30% default probability")
        print(f"  Test 6 PASSED: High-risk default probability = {default_prob:.2%}")
    
    def test_7_risk_level_determination(self):
        """Test 7: Risk level determination from default probability"""
        test_cases = [
            (0.05, "Low"),
            (0.15, "Medium"),
            (0.35, "High"),
            (0.60, "Critical"),
        ]
        
        for prob, expected_level in test_cases:
            level, score = self.agent._determine_risk_level(prob)  # Returns tuple
            self.assertEqual(level, expected_level, f"Prob {prob} should be {expected_level}")
        
        print(f"  Test 7 PASSED: All risk level thresholds correct")


# =============================================================================
# TEST 8-10: FRAUD DETECTION AGENT TESTS
# =============================================================================

class TestFraudDetectionAgent(unittest.TestCase):
    """Tests for the FraudDetectionAgent"""
    
    def setUp(self):
        self.agent = FraudDetectionAgent()
    
    def test_8_synthetic_identity_scoring_clean(self):
        """Test 8: Synthetic identity check for clean application"""
        application = get_low_risk_application()
        
        score = self.agent._check_synthetic_identity(application)
        
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        print(f"  Test 8 PASSED: Synthetic identity score = {score:.2%}")
    
    def test_9_anomaly_detection(self):
        """Test 9: Anomaly detection in application data"""
        application = get_low_risk_application()
        
        anomalies = self.agent._check_anomalies(application)
        
        self.assertIsInstance(anomalies, dict)
        self.assertIn("score", anomalies)  # Returns 'score' not 'anomaly_score'
        print(f"  Test 9 PASSED: Anomaly check returned score={anomalies.get('score', 'N/A')}")
    
    def test_10_velocity_check(self):
        """Test 10: Velocity check simulation"""
        application = get_low_risk_application()
        
        velocity = self.agent._check_velocity(application)
        
        self.assertIsInstance(velocity, dict)
        self.assertIn("passed", velocity)  # Returns 'passed' boolean
        print(f"  Test 10 PASSED: Velocity check passed = {velocity.get('passed', 'N/A')}")


# =============================================================================
# TEST 11-13: INCOME VERIFICATION AGENT TESTS
# =============================================================================

class TestIncomeVerificationAgent(unittest.TestCase):
    """Tests for the IncomeVerificationAgent"""
    
    def setUp(self):
        self.agent = IncomeVerificationAgent()
    
    def test_11_dti_calculation(self):
        """Test 11: DTI ratio calculation"""
        application = get_low_risk_application()
        
        dti = self.agent._calculate_dti(application)
        
        self.assertGreaterEqual(dti, 0.0)
        self.assertLessEqual(dti, 1.0)
        print(f"  Test 11 PASSED: DTI ratio = {dti:.2%}")
    
    def test_12_income_verification_status(self):
        """Test 12: Income verification against documents"""
        application = get_low_risk_application()
        stated_income = application.get("employment", {}).get("annual_income", 50000)
        
        # Create mock document results
        doc_results = {"pay_stub": {"monthly_income": stated_income / 12}}
        
        variance = self.agent._verify_income(stated_income, doc_results)
        
        self.assertIsInstance(variance, float)
        print(f"  Test 12 PASSED: Income variance = {variance:.2%}")
    
    def test_13_employment_stability(self):
        """Test 13: Employment stability scoring"""
        application = get_low_risk_application()
        employment = application.get("employment", {})
        
        stability = self.agent._assess_employment_stability(employment)
        
        # Returns 0-100 scale, not 0-1
        self.assertGreaterEqual(stability, 0.0)
        self.assertLessEqual(stability, 100.0)
        print(f"  Test 13 PASSED: Employment stability = {stability}%")


# =============================================================================
# TEST 14-16: CREDIT HISTORY AGENT TESTS
# =============================================================================

class TestCreditHistoryAgent(unittest.TestCase):
    """Tests for the CreditHistoryAgent"""
    
    def setUp(self):
        self.agent = CreditHistoryAgent()
    
    def test_14_credit_quality_assessment(self):
        """Test 14: Credit quality assessment based on credit data"""
        application = get_low_risk_application()
        credit = application.get("credit", {})
        
        quality = self.agent._assess_credit_quality(credit)
        
        self.assertIn(quality, ["excellent", "good", "fair", "poor", "very_poor"])
        print(f"  Test 14 PASSED: Credit quality = {quality}")
    
    def test_15_payment_behavior_analysis(self):
        """Test 15: Payment behavior prediction"""
        application = get_low_risk_application()
        credit = application.get("credit", {})
        
        behavior = self.agent._predict_payment_behavior(credit)
        
        # Returns a string description, not a dict
        self.assertIsInstance(behavior, str)
        self.assertGreater(len(behavior), 5)
        print(f"  Test 15 PASSED: Payment behavior prediction = {behavior}")
    
    def test_16_credit_trajectory(self):
        """Test 16: Credit trajectory analysis"""
        application = get_low_risk_application()
        credit = application.get("credit", {})
        
        trajectory = self.agent._assess_credit_trajectory(credit)
        
        # Returns a string, not a dict
        self.assertIsInstance(trajectory, str)
        self.assertIn(trajectory, ["improving", "stable", "declining", "insufficient_history"])
        print(f"  Test 16 PASSED: Credit trajectory = {trajectory}")


# =============================================================================
# TEST 17-20: CHIEF UNDERWRITER AGENT TESTS
# =============================================================================

class TestChiefUnderwriterAgent(unittest.TestCase):
    """Tests for the ChiefUnderwriterAgent"""
    
    def setUp(self):
        self.agent = ChiefUnderwriterAgent()
    
    def test_17_weighted_confidence_calculation(self):
        """Test 17: Weighted confidence aggregation from all agents"""
        agent_results = get_mock_agent_results("low")
        
        weighted_conf = self.agent._calculate_weighted_confidence(agent_results)
        
        self.assertGreaterEqual(weighted_conf, 0.5)
        self.assertLessEqual(weighted_conf, 1.0)
        print(f"  Test 17 PASSED: Weighted confidence = {weighted_conf:.2%}")
    
    def test_18_risk_metrics_low_risk(self):
        """Test 18: Risk metrics calculation for low-risk applicant"""
        agent_results = get_mock_agent_results("low")
        
        default_prob, risk_level, percentile = self.agent._calculate_risk_metrics(agent_results)
        
        self.assertLess(default_prob, 0.15, "Low-risk should have low default prob")
        self.assertEqual(risk_level, "Low")
        print(f"  Test 18 PASSED: Low-risk metrics - default_prob={default_prob:.2%}, level={risk_level}")
    
    def test_19_interest_rate_calculation(self):
        """Test 19: Interest rate calculation based on risk"""
        # Method returns decimal rate (e.g., 0.075 = 7.5%)
        test_cases = [
            (0.05, "Low", 60, 0.05, 0.10),     # Low risk: 5-10%
            (0.20, "Medium", 60, 0.08, 0.16),  # Medium risk: 8-16%
            (0.45, "High", 60, 0.14, 0.24),   # High risk: 14-24%
        ]
        
        for default_prob, risk_level, loan_term, min_rate, max_rate in test_cases:
            rate = self.agent._calculate_interest_rate(default_prob, risk_level, loan_term)
            self.assertGreaterEqual(rate, min_rate, f"Rate {rate} should be >= {min_rate}")
            self.assertLessEqual(rate, max_rate, f"Rate {rate} should be <= {max_rate}")
        
        print(f"  Test 19 PASSED: Interest rate calculations within expected ranges")
    
    def test_20_risk_percentile_calculation(self):
        """Test 20: Risk percentile within risk class"""
        # Percentile is 0-100 based on position within risk class
        test_cases = [
            (0.03, "Low", 0, 100),      # Valid range for Low class
            (0.15, "Medium", 0, 100),   # Valid range for Medium class
            (0.55, "Critical", 0, 100), # Valid range for Critical class
        ]
        
        for default_prob, risk_level, min_pct, max_pct in test_cases:
            percentile = self.agent._calculate_risk_percentile(default_prob, risk_level)
            self.assertGreaterEqual(percentile, min_pct)
            self.assertLessEqual(percentile, max_pct)
        
        print(f"  Test 20 PASSED: Risk percentile calculations within expected ranges")


# =============================================================================
# TEST 21-22: COMPLIANCE AGENT TESTS
# =============================================================================

class TestComplianceAgent(unittest.TestCase):
    """Tests for the ComplianceAgent"""
    
    def setUp(self):
        self.agent = ComplianceAgent()
    
    def test_21_fcra_compliance_check(self):
        """Test 21: FCRA compliance verification"""
        application = get_low_risk_application()
        context = {"previous_results": get_mock_agent_results("low")}
        
        result = self.agent._check_fcra_compliance(application, context)
        
        # Returns dict with 'compliant' (bool) and 'findings' (list)
        self.assertIsInstance(result, dict)
        self.assertIn("compliant", result)
        self.assertIn("findings", result)
        self.assertIsInstance(result["compliant"], bool)
        self.assertIsInstance(result["findings"], list)
        print(f"  Test 21 PASSED: FCRA compliant={result['compliant']}, findings={len(result['findings'])}")
    
    def test_22_adverse_action_reasons(self):
        """Test 22: Adverse action reason generation for denial"""
        application = get_high_risk_application()
        context = {"previous_results": get_mock_agent_results("high")}
        
        reasons = self.agent._prepare_adverse_action_reasons(application, context)
        
        self.assertIsInstance(reasons, list)
        print(f"  Test 22 PASSED: Generated {len(reasons)} adverse action reasons")


# =============================================================================
# TEST 23-24: COLLATERAL AGENT TESTS
# =============================================================================

class TestCollateralAgent(unittest.TestCase):
    """Tests for the CollateralAgent"""
    
    def setUp(self):
        self.agent = CollateralAgent()
    
    def test_23_collateral_value_estimation(self):
        """Test 23: Collateral value estimation"""
        # Test _estimate_value method
        estimated_value, confidence = self.agent._estimate_value("real_estate", 500000)
        
        self.assertGreater(estimated_value, 0)
        self.assertGreaterEqual(confidence, 0.5)
        self.assertLessEqual(confidence, 1.0)
        print(f"  Test 23 PASSED: Estimated value=${estimated_value:,.0f}, confidence={confidence:.2%}")
    
    def test_24_collateral_quality(self):
        """Test 24: Collateral quality assessment"""
        # Test _assess_quality method
        quality = self.agent._assess_quality("real_estate", 0.75, 0.90)
        
        self.assertIn(quality, ["excellent", "good", "fair", "poor"])
        print(f"  Test 24 PASSED: Collateral quality = {quality}")


# =============================================================================
# TEST 25-26: DOCUMENT INTELLIGENCE AGENT TESTS
# =============================================================================

class TestDocumentIntelligenceAgent(unittest.TestCase):
    """Tests for the DocumentIntelligenceAgent"""
    
    def setUp(self):
        self.agent = DocumentIntelligenceAgent()
    
    def test_25_document_simulation(self):
        """Test 25: Document extraction simulation"""
        application = get_low_risk_application()
        
        # Test _simulate_extraction
        extraction = self.agent._simulate_extraction(application, "pay_stub")
        
        self.assertIsInstance(extraction, dict)
        print(f"  Test 25 PASSED: Document extraction simulated")
    
    def test_26_cross_reference_check(self):
        """Test 26: Cross-reference application data with documents"""
        application = get_low_risk_application()
        
        # Create mock verification results
        verification_results = [
            {"doc_type": "pay_stub", "verified": True, "extracted_data": {"monthly_income": 8000}},
            {"doc_type": "bank_statement", "verified": True, "extracted_data": {"average_balance": 50000}}
        ]
        
        matches = self.agent._cross_reference_data(application, verification_results)
        
        self.assertIsInstance(matches, dict)
        print(f"  Test 26 PASSED: Cross-reference check complete")


# =============================================================================
# TEST 27-28: MARKET CONDITIONS AGENT TESTS
# =============================================================================

class TestMarketConditionsAgent(unittest.TestCase):
    """Tests for the MarketConditionsAgent"""
    
    def setUp(self):
        self.agent = MarketConditionsAgent()
    
    def test_27_economic_risk_factor(self):
        """Test 27: Economic risk factor calculation"""
        economic_factor = self.agent._calculate_economic_risk()
        
        self.assertGreaterEqual(economic_factor, 0.0)
        self.assertLessEqual(economic_factor, 1.0)
        print(f"  Test 27 PASSED: Economic risk factor = {economic_factor:.2%}")
    
    def test_28_sector_risk_assessment(self):
        """Test 28: Sector-specific risk assessment"""
        application = get_low_risk_application()
        loan_purpose = application.get("loan", {}).get("purpose", "home_purchase")
        
        sector_risk = self.agent._assess_sector_risk(loan_purpose)
        
        # Returns a string like "low", "moderate", "high"
        self.assertIsInstance(sector_risk, str)
        self.assertIn(sector_risk, ["low", "moderate", "high", "very_high"])
        print(f"  Test 28 PASSED: Sector risk = {sector_risk}")


# =============================================================================
# TEST 29-30: EXPLAINABILITY AGENT TESTS
# =============================================================================

class TestExplainabilityAgent(unittest.TestCase):
    """Tests for the ExplainabilityAgent"""
    
    def setUp(self):
        self.agent = ExplainabilityAgent()
    
    def test_29_next_steps_generation(self):
        """Test 29: Generate next steps based on decision"""
        chief_result = {
            "decision": "APPROVE",
            "loan_terms": {"amount": 250000, "rate": 6.5}
        }
        
        next_steps = self.agent._generate_next_steps("APPROVE", chief_result)
        
        self.assertIsInstance(next_steps, str)
        self.assertGreater(len(next_steps), 20)
        print(f"  Test 29 PASSED: Generated next steps ({len(next_steps)} chars)")
    
    def test_30_faq_generation(self):
        """Test 30: Generate FAQ based on decision"""
        faq = self.agent._generate_faq("DENY")
        
        self.assertIsInstance(faq, list)
        self.assertGreater(len(faq), 0)
        for item in faq:
            self.assertIn("question", item)
            self.assertIn("answer", item)
        print(f"  Test 30 PASSED: Generated {len(faq)} FAQ items")


# =============================================================================
# RUN ALL TESTS
# =============================================================================

def run_all_tests():
    """Run all 30 unit tests and report results"""
    print("=" * 70)
    print("RUNNING 30 AGENT UNIT TESTS")
    print("=" * 70)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestConfidenceCalculator,
        TestQuantitativeRiskAgent,
        TestFraudDetectionAgent,
        TestIncomeVerificationAgent,
        TestCreditHistoryAgent,
        TestChiefUnderwriterAgent,
        TestComplianceAgent,
        TestCollateralAgent,
        TestDocumentIntelligenceAgent,
        TestMarketConditionsAgent,
        TestExplainabilityAgent,
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailed tests:")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print("\nTests with errors:")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    if result.wasSuccessful():
        print("\n" + "=" * 70)
        print("ALL 30 TESTS PASSED!")
        print("=" * 70)
    
    return result


if __name__ == "__main__":
    run_all_tests()
