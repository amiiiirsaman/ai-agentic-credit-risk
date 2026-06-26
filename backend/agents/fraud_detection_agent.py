"""
Fraud Detection Agent - Synthetic identity and anomaly detection
"""
import json
from typing import Dict, Any, List
import hashlib
from .base_agent import BaseAgent
from .confidence_calculator import ConfidenceCalculator

class FraudDetectionAgent(BaseAgent):
    """
    Fraud Detection Agent
    
    Responsibilities:
    - Detect synthetic identity fraud patterns
    - Identify application anomalies
    - Velocity checks
    - Cross-reference fraud indicators
    """
    
    def __init__(self):
        super().__init__(
            name="FraudDetection",
            description="Fraud and anomaly detection specialist"
        )
    
    async def process(self, application_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform fraud detection analysis"""
        
        # Run fraud detection checks
        synthetic_id_score = self._check_synthetic_identity(application_data)
        anomaly_indicators = self._check_anomalies(application_data)
        velocity_check = self._check_velocity(application_data)
        
        # Aggregate fraud indicators
        all_indicators = []
        all_indicators.extend(anomaly_indicators.get("indicators", []))
        
        if synthetic_id_score > 30:
            all_indicators.append(f"Elevated synthetic identity risk: {synthetic_id_score}")
        
        if not velocity_check.get("passed", True):
            all_indicators.extend(velocity_check.get("flags", []))
        
        # Calculate overall fraud risk
        base_risk = synthetic_id_score * 0.4 + anomaly_indicators.get("score", 0) * 0.4
        if not velocity_check.get("passed", True):
            base_risk += 20
        
        fraud_risk_score = min(100, base_risk)
        
        # Get LLM analysis (may return None on failure)
        llm_analysis = await self._get_llm_analysis(
            application_data, 
            synthetic_id_score,
            anomaly_indicators,
            velocity_check,
            all_indicators
        ) or {}
        
        # Determine risk level
        if fraud_risk_score < 20:
            risk_level = "low"
        elif fraud_risk_score < 40:
            risk_level = "medium"
        elif fraud_risk_score < 70:
            risk_level = "high"
        else:
            risk_level = "critical"
        
        # Calculate dynamic confidence based on data quality and analysis
        confidence = self._calculate_confidence(
            application_data, llm_analysis, fraud_risk_score, all_indicators
        )
        
        return {
            "fraud_risk_score": round(fraud_risk_score, 2),
            "risk_level": risk_level,
            "synthetic_identity_score": round(synthetic_id_score, 2),
            "fraud_indicators": all_indicators,
            "velocity_check_passed": velocity_check.get("passed", True),
            "anomaly_details": anomaly_indicators,
            "recommendation": llm_analysis.get("recommendation", "") if llm_analysis else "",
            "detailed_analysis": llm_analysis.get("detailed_analysis", "") if llm_analysis else "",
            "confidence": confidence,
            "reasoning": llm_analysis.get("reasoning", "") if llm_analysis else ""
        }
    
    def _calculate_confidence(self, data: Dict, llm_output: Dict, risk_score: float, indicators: List) -> float:
        """Calculate dynamic confidence based on analysis quality"""
        # Base confidence from data completeness
        required_fields = ["applicant.name", "applicant.age", "credit.credit_score", "employment.annual_income"]
        completeness = ConfidenceCalculator.calculate_data_completeness(data, required_fields)
        
        # Analysis quality from LLM output
        expected_keys = ["recommendation", "reasoning", "detailed_analysis"]
        analysis_quality = ConfidenceCalculator.calculate_analysis_quality(
            llm_output, expected_keys, has_reasoning=bool(llm_output.get("reasoning"))
        )
        
        # Adjust based on risk findings - clearer signals = higher confidence
        if risk_score < 15 or risk_score > 70:  # Clear low or high risk
            signal_clarity = 1.0
        elif risk_score < 30 or risk_score > 50:  # Moderate clarity
            signal_clarity = 0.9
        else:  # Ambiguous middle range
            signal_clarity = 0.8
        
        # More indicators found = more thorough analysis = higher confidence
        indicator_bonus = min(0.1, len(indicators) * 0.02)
        
        confidence = (completeness * 0.25 + analysis_quality * 0.35 + signal_clarity * 0.40) + indicator_bonus
        return round(max(0.55, min(0.96, confidence)), 4)
    
    def _check_synthetic_identity(self, application_data: Dict[str, Any]) -> float:
        """Check for synthetic identity fraud patterns"""
        
        score = 0
        applicant = application_data.get("applicant", {})
        credit = application_data.get("credit", {})
        employment = application_data.get("employment", {})
        
        age = applicant.get("age", 30)
        credit_history_years = credit.get("years_credit_history", 0)
        
        # Age vs credit history mismatch
        expected_max_history = age - 18
        if credit_history_years > expected_max_history:
            score += 25
        
        # Very new credit file with multiple inquiries
        if credit_history_years < 2 and credit.get("hard_inquiries_6mo", 0) > 3:
            score += 20
        
        # Perfect credit with no history
        if credit.get("credit_score", 0) > 750 and credit_history_years < 3:
            score += 15
        
        # Income doesn't match job title expectations (simplified check)
        income = employment.get("annual_income", 0)
        years_employed = employment.get("years_employed", 0)
        
        # Suspiciously high income for very short employment
        if income > 200000 and years_employed < 1:
            score += 20
        
        # No delinquencies with short history (too clean)
        if credit_history_years < 3 and credit.get("delinquencies_2yrs", 0) == 0 and credit.get("credit_score", 0) > 700:
            score += 10
        
        return min(100, score)
    
    def _check_anomalies(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check for application anomalies"""
        
        indicators = []
        score = 0
        
        employment = application_data.get("employment", {})
        financial = application_data.get("financial", {})
        credit = application_data.get("credit", {})
        loan = application_data.get("loan", {})
        
        # Income anomalies
        annual_income = employment.get("annual_income", 0)
        monthly_debt = financial.get("monthly_debt", 0)
        savings = financial.get("savings", 0)
        
        # Very high income with no savings
        if annual_income > 150000 and savings < 5000:
            indicators.append("High income with minimal savings")
            score += 15
        
        # Loan amount much higher than income
        loan_to_income = loan.get("amount", 0) / max(annual_income, 1)
        if loan_to_income > 8:
            indicators.append(f"Loan amount is {loan_to_income:.1f}x annual income")
            score += 20
        
        # Credit utilization anomalies
        utilization = credit.get("credit_utilization", 0)
        if utilization > 90:
            indicators.append(f"Very high credit utilization: {utilization}%")
            score += 15
        
        # Round number anomalies (could indicate fabricated data)
        if annual_income % 10000 == 0 and annual_income > 50000:
            indicators.append("Income is suspiciously round number")
            score += 5
        
        # Employment status mismatch
        if employment.get("status") == "employed" and not employment.get("employer_name"):
            indicators.append("Employed status but no employer provided")
            score += 10
        
        return {
            "indicators": indicators,
            "score": score
        }
    
    def _check_velocity(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check velocity patterns (simulated for synthetic data)"""
        
        # In production, this would check actual application velocity
        # For synthetic data, we simulate based on inquiry count
        
        credit = application_data.get("credit", {})
        inquiries = credit.get("hard_inquiries_6mo", 0)
        
        flags = []
        passed = True
        
        if inquiries > 5:
            flags.append(f"High number of credit inquiries: {inquiries} in 6 months")
            passed = False
        
        if inquiries > 3:
            flags.append("Multiple recent credit applications detected")
        
        return {
            "passed": passed,
            "flags": flags,
            "inquiry_count": inquiries
        }
    
    async def _get_llm_analysis(
        self,
        application_data: Dict[str, Any],
        synthetic_score: float,
        anomaly_indicators: Dict,
        velocity_check: Dict,
        all_indicators: List[str]
    ) -> Dict[str, Any]:
        """Get LLM analysis for fraud detection"""
        
        system_prompt = """You are a fraud detection specialist with expertise in 
identifying synthetic identity fraud, application fraud, and financial anomalies.
Analyze the fraud detection results and provide insights."""
        
        applicant = application_data.get("applicant", {})
        employment = application_data.get("employment", {})
        credit = application_data.get("credit", {})
        
        prompt = f"""Analyze these fraud detection results:

Applicant Profile:
- Name: {applicant.get('name')}
- Age: {applicant.get('age')}
- Annual Income: ${employment.get('annual_income', 0):,.2f}
- Credit Score: {credit.get('credit_score')}
- Years of Credit History: {credit.get('years_credit_history')}

Fraud Detection Results:
- Synthetic Identity Score: {synthetic_score}/100
- Anomaly Score: {anomaly_indicators.get('score', 0)}/100
- Velocity Check Passed: {velocity_check.get('passed')}

All Fraud Indicators:
{json.dumps(all_indicators, indent=2) if all_indicators else "No significant indicators"}

Provide analysis in JSON format:
{{
    "recommendation": "PROCEED" | "REVIEW" | "REJECT",
    "detailed_analysis": "explanation of fraud risk assessment",
    "additional_verification_needed": ["list of recommended additional verifications"],
    "reasoning": "detailed reasoning for the recommendation"
}}"""
        
        return self.bedrock.invoke_with_json_output(prompt, system_prompt)
