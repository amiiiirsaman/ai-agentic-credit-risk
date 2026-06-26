"""
Credit History Agent - Credit report analysis
"""
import json
from typing import Dict, Any, List
from .base_agent import BaseAgent
from .confidence_calculator import ConfidenceCalculator, CREDIT_VALIDATION_RULES

class CreditHistoryAgent(BaseAgent):
    """
    Credit History Analyst Agent
    
    Responsibilities:
    - Analyze credit report data
    - Assess payment behavior patterns
    - Evaluate credit trajectory
    - Identify credit concerns
    """
    
    def __init__(self):
        super().__init__(
            name="CreditHistory",
            description="Credit report analysis and payment behavior specialist"
        )
    
    async def process(self, application_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze credit history"""
        
        credit = application_data.get("credit", {})
        
        # Determine credit quality
        credit_quality = self._assess_credit_quality(credit)
        
        # Predict payment behavior
        payment_prediction = self._predict_payment_behavior(credit)
        
        # Assess credit trajectory
        trajectory = self._assess_credit_trajectory(credit)
        
        # Identify key findings
        findings = self._identify_key_findings(credit)
        
        # Get LLM analysis (may return None on failure)
        llm_analysis = await self._get_llm_analysis(
            application_data,
            credit_quality,
            payment_prediction,
            trajectory,
            findings
        ) or {}
        
        # Calculate dynamic confidence
        confidence = self._calculate_confidence(application_data, llm_analysis, credit_quality)
        
        return {
            "credit_score": credit.get("credit_score", 0),
            "credit_quality": credit_quality,
            "credit_quality_score": self._quality_to_score(credit_quality),
            "payment_behavior_prediction": payment_prediction,
            "credit_trajectory": trajectory,
            "years_credit_history": credit.get("years_credit_history", 0),
            "num_credit_lines": credit.get("num_credit_lines", 0),
            "credit_utilization": credit.get("credit_utilization", 0),
            "delinquencies_2yrs": credit.get("delinquencies_2yrs", 0),
            "public_records": credit.get("public_records", 0),
            "hard_inquiries_6mo": credit.get("hard_inquiries_6mo", 0),
            "key_findings": findings,
            "credit_strengths": llm_analysis.get("strengths", []) if llm_analysis else [],
            "credit_concerns": llm_analysis.get("concerns", []) if llm_analysis else [],
            "recommendation": llm_analysis.get("recommendation", "") if llm_analysis else "",
            "confidence": confidence,
            "reasoning": llm_analysis.get("reasoning", "") if llm_analysis else ""
        }
    
    def _calculate_confidence(self, data: Dict, llm_output: Dict, credit_quality: str) -> float:
        """Calculate dynamic confidence based on data quality and analysis"""
        required_fields = ["credit.credit_score", "credit.years_credit_history"]
        optional_fields = ["credit.delinquencies_2yrs", "credit.credit_utilization", "credit.public_records"]
        
        completeness = ConfidenceCalculator.calculate_data_completeness(data, required_fields, optional_fields)
        validity = ConfidenceCalculator.calculate_value_validity(data, CREDIT_VALIDATION_RULES)
        
        expected_keys = ["strengths", "concerns", "recommendation", "reasoning"]
        analysis_quality = ConfidenceCalculator.calculate_analysis_quality(
            llm_output, expected_keys, has_reasoning=bool(llm_output.get("reasoning"))
        )
        
        # Clearer credit profiles = higher confidence
        quality_clarity = {"excellent": 0.95, "good": 0.90, "fair": 0.85, "poor": 0.88, "very_poor": 0.92}
        clarity_score = quality_clarity.get(credit_quality, 0.85)
        
        confidence = completeness * 0.20 + validity * 0.25 + analysis_quality * 0.30 + clarity_score * 0.25
        return round(max(0.60, min(0.96, confidence)), 4)
    
    def _assess_credit_quality(self, credit: Dict) -> str:
        """Determine overall credit quality"""
        
        score = credit.get("credit_score", 0)
        delinquencies = credit.get("delinquencies_2yrs", 0)
        public_records = credit.get("public_records", 0)
        
        # Score-based quality
        if score >= 750:
            quality = "excellent"
        elif score >= 700:
            quality = "good"
        elif score >= 650:
            quality = "fair"
        elif score >= 580:
            quality = "poor"
        else:
            quality = "very_poor"
        
        # Adjust for negative items
        if public_records > 0:
            # Downgrade one level
            quality_order = ["excellent", "good", "fair", "poor", "very_poor"]
            idx = quality_order.index(quality)
            if idx < len(quality_order) - 1:
                quality = quality_order[idx + 1]
        
        if delinquencies >= 3:
            quality_order = ["excellent", "good", "fair", "poor", "very_poor"]
            idx = quality_order.index(quality)
            if idx < len(quality_order) - 1:
                quality = quality_order[idx + 1]
        
        return quality
    
    def _quality_to_score(self, quality: str) -> int:
        """Convert quality assessment to numeric score"""
        scores = {
            "excellent": 95,
            "good": 80,
            "fair": 65,
            "poor": 45,
            "very_poor": 25
        }
        return scores.get(quality, 50)
    
    def _predict_payment_behavior(self, credit: Dict) -> str:
        """Predict future payment behavior"""
        
        score = credit.get("credit_score", 0)
        delinquencies = credit.get("delinquencies_2yrs", 0)
        utilization = credit.get("credit_utilization", 0)
        
        # Risk factors
        risk_points = 0
        
        if score < 650:
            risk_points += 3
        elif score < 700:
            risk_points += 1
        
        risk_points += delinquencies * 2
        
        if utilization > 80:
            risk_points += 2
        elif utilization > 50:
            risk_points += 1
        
        if risk_points == 0:
            return "excellent - very low risk of late payments"
        elif risk_points <= 2:
            return "good - low risk of payment issues"
        elif risk_points <= 4:
            return "fair - moderate risk of occasional late payments"
        elif risk_points <= 6:
            return "concerning - elevated risk of payment problems"
        else:
            return "poor - high risk of payment delinquency"
    
    def _assess_credit_trajectory(self, credit: Dict) -> str:
        """Assess credit trajectory (improving, stable, declining)"""
        
        inquiries = credit.get("hard_inquiries_6mo", 0)
        delinquencies = credit.get("delinquencies_2yrs", 0)
        utilization = credit.get("credit_utilization", 0)
        history_years = credit.get("years_credit_history", 0)
        
        # Positive indicators
        positive = 0
        negative = 0
        
        if utilization < 30:
            positive += 1
        elif utilization > 70:
            negative += 1
        
        if inquiries == 0:
            positive += 1
        elif inquiries > 3:
            negative += 1
        
        if delinquencies == 0:
            positive += 1
        else:
            negative += delinquencies
        
        if history_years > 7:
            positive += 1
        
        if positive > negative + 1:
            return "improving"
        elif negative > positive + 1:
            return "declining"
        else:
            return "stable"
    
    def _identify_key_findings(self, credit: Dict) -> List[str]:
        """Identify key credit findings"""
        
        findings = []
        
        score = credit.get("credit_score", 0)
        if score >= 750:
            findings.append(f"Excellent credit score of {score}")
        elif score >= 700:
            findings.append(f"Good credit score of {score}")
        elif score < 650:
            findings.append(f"Below-average credit score of {score} may affect terms")
        
        history = credit.get("years_credit_history", 0)
        if history >= 10:
            findings.append(f"Established credit history of {history} years")
        elif history < 3:
            findings.append(f"Limited credit history of only {history} years")
        
        utilization = credit.get("credit_utilization", 0)
        if utilization > 70:
            findings.append(f"High credit utilization at {utilization}%")
        elif utilization < 30:
            findings.append(f"Healthy credit utilization at {utilization}%")
        
        delinquencies = credit.get("delinquencies_2yrs", 0)
        if delinquencies > 0:
            findings.append(f"{delinquencies} delinquencies in past 2 years")
        else:
            findings.append("Clean payment history with no recent delinquencies")
        
        public_records = credit.get("public_records", 0)
        if public_records > 0:
            findings.append(f"{public_records} public record(s) on file")
        
        inquiries = credit.get("hard_inquiries_6mo", 0)
        if inquiries > 3:
            findings.append(f"Multiple recent credit inquiries ({inquiries} in 6 months)")
        
        return findings
    
    async def _get_llm_analysis(
        self,
        application_data: Dict[str, Any],
        credit_quality: str,
        payment_prediction: str,
        trajectory: str,
        findings: List[str]
    ) -> Dict[str, Any]:
        """Get LLM analysis for credit history"""
        
        system_prompt = """You are a credit analyst with deep expertise in credit report 
analysis, credit scoring models, and payment behavior prediction."""
        
        credit = application_data.get("credit", {})
        loan = application_data.get("loan", {})
        
        prompt = f"""Analyze this credit profile:

Credit Information:
- Credit Score: {credit.get('credit_score')}
- Years of Credit History: {credit.get('years_credit_history')}
- Number of Credit Lines: {credit.get('num_credit_lines')}
- Credit Utilization: {credit.get('credit_utilization')}%
- Delinquencies (2 years): {credit.get('delinquencies_2yrs')}
- Public Records: {credit.get('public_records')}
- Hard Inquiries (6 months): {credit.get('hard_inquiries_6mo')}

Analysis Results:
- Credit Quality: {credit_quality}
- Payment Behavior Prediction: {payment_prediction}
- Credit Trajectory: {trajectory}

Key Findings:
{json.dumps(findings, indent=2)}

Loan Request: ${loan.get('amount', 0):,.2f} for {loan.get('purpose')}

Provide analysis in JSON format:
{{
    "strengths": ["list credit profile strengths"],
    "concerns": ["list credit profile concerns"],
    "recommendation": "APPROVE" | "CONDITIONAL" | "DENY based on credit",
    "suggested_conditions": ["any conditions to mitigate credit risk"],
    "reasoning": "detailed explanation of credit analysis"
}}"""
        
        return self.bedrock.invoke_with_json_output(prompt, system_prompt)
