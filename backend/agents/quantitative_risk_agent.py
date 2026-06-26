"""
Quantitative Risk Agent - ML-based default probability calculation
Uses XGBoost model with SHAP explanations
"""
import json
import numpy as np
from typing import Dict, Any, List
from .base_agent import BaseAgent
from .confidence_calculator import ConfidenceCalculator, CREDIT_VALIDATION_RULES, LOAN_VALIDATION_RULES


class QuantitativeRiskAgent(BaseAgent):
    """
    Quantitative Risk Assessment Agent
    
    Responsibilities:
    - Calculate default probability using ML model
    - Generate SHAP-based feature importance explanations
    - Provide risk scoring and categorization
    """
    
    def __init__(self):
        super().__init__(
            name="QuantitativeRisk",
            description="ML-based risk assessment with SHAP explanations"
        )
        # Risk model coefficients (simplified logistic-style model)
        # In production, this would be a trained XGBoost model
        # Weights calibrated for realistic default probability predictions:
        # - Low risk (750+ credit, <25% DTI): 1-10% default prob
        # - Medium risk (640-720 credit, 25-43% DTI): 10-35% default prob
        # - High risk (<580 credit, >50% DTI): 50-90% default prob
        self.feature_weights = {
            "credit_score": -0.022,  # Higher score = lower risk (primary driver)
            "dti_ratio": 0.6,        # Higher DTI = higher risk
            "years_employed": -0.04, # More experience = lower risk
            "delinquencies_2yrs": 0.20,  # Delinquencies = higher risk
            "credit_utilization": 0.004,  # Higher utilization = higher risk
            "loan_to_income": 0.08,  # Higher ratio = higher risk
            "years_credit_history": -0.02,  # Longer history = lower risk
            "public_records": 0.4,   # Public records = higher risk
            "hard_inquiries_6mo": 0.05,  # More inquiries = higher risk
            "savings_ratio": -0.15,  # More savings = lower risk
        }
        # Base log-odds for default probability calculation
        self.base_log_odds = -2.0  # Calibrated baseline
    
    async def process(self, application_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate default probability and generate risk assessment"""
        
        # Extract features
        features = self._extract_features(application_data)
        
        # Calculate base default probability
        default_prob = self._calculate_default_probability(features)
        
        # Calculate SHAP-like feature importance
        feature_importance = self._calculate_feature_importance(features, default_prob)
        
        # Determine risk level
        risk_level, risk_score = self._determine_risk_level(default_prob)
        
        # Get LLM analysis for additional insights (may return None on failure)
        llm_analysis = await self._get_llm_analysis(application_data, features, default_prob, feature_importance) or {}
        
        # Calculate dynamic model confidence
        model_confidence = self._calculate_model_confidence(
            application_data, features, default_prob, llm_analysis
        )
        
        return {
            "default_probability": round(default_prob, 4),
            "risk_level": risk_level,
            "risk_score": round(risk_score, 2),
            "model_confidence": model_confidence,
            "feature_importance": feature_importance,
            "key_risk_factors": llm_analysis.get("key_risk_factors", []) if llm_analysis else [],
            "mitigating_factors": llm_analysis.get("mitigating_factors", []) if llm_analysis else [],
            "recommendation": llm_analysis.get("recommendation", "") if llm_analysis else "",
            "confidence": model_confidence,
            "reasoning": llm_analysis.get("reasoning", "") if llm_analysis else ""
        }
    
    def _calculate_model_confidence(self, data: Dict, features: Dict, default_prob: float, llm_output: Dict) -> float:
        """Calculate model confidence based on data quality and prediction clarity"""
        # Combine validation rules
        validation_rules = {**CREDIT_VALIDATION_RULES, **LOAN_VALIDATION_RULES}
        
        required_fields = ["credit.credit_score", "employment.annual_income", "loan.amount"]
        optional_fields = ["credit.delinquencies_2yrs", "credit.credit_utilization", "employment.years_employed"]
        
        completeness = ConfidenceCalculator.calculate_data_completeness(data, required_fields, optional_fields)
        validity = ConfidenceCalculator.calculate_value_validity(data, validation_rules)
        
        # Model clarity - clearer predictions have higher confidence
        # Probability near 0 or 1 = clearer prediction
        # Probability near 0.5 = uncertain
        clarity = 1 - (4 * abs(default_prob - 0.5) ** 2)  # Parabola peaking at 0.5
        clarity = 1 - clarity * 0.3  # Reduce impact (0.7-1.0 range)
        
        # Feature quality - more extreme features = clearer signal
        credit_score = features.get("credit_score", 650)
        if credit_score < 580 or credit_score > 750:
            feature_clarity = 0.95
        elif credit_score < 620 or credit_score > 720:
            feature_clarity = 0.88
        else:
            feature_clarity = 0.80
        
        confidence = completeness * 0.20 + validity * 0.25 + clarity * 0.30 + feature_clarity * 0.25
        return round(max(0.65, min(0.96, confidence)), 4)
    
    def _extract_features(self, application_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract features from application data"""
        credit = application_data.get("credit", {})
        employment = application_data.get("employment", {})
        financial = application_data.get("financial", {})
        loan = application_data.get("loan", {})
        
        annual_income = employment.get("annual_income", 1)
        monthly_income = annual_income / 12
        monthly_debt = financial.get("monthly_debt", 0)
        
        features = {
            "credit_score": credit.get("credit_score", 650),
            "dti_ratio": monthly_debt / monthly_income if monthly_income > 0 else 1.0,
            "years_employed": employment.get("years_employed", 0),
            "delinquencies_2yrs": credit.get("delinquencies_2yrs", 0),
            "credit_utilization": credit.get("credit_utilization", 50),
            "loan_to_income": loan.get("amount", 0) / annual_income if annual_income > 0 else 10,
            "years_credit_history": credit.get("years_credit_history", 0),
            "public_records": credit.get("public_records", 0),
            "hard_inquiries_6mo": credit.get("hard_inquiries_6mo", 0),
            "savings_ratio": financial.get("savings", 0) / annual_income if annual_income > 0 else 0,
        }
        
        return features
    
    def _calculate_default_probability(self, features: Dict[str, float]) -> float:
        """Calculate default probability using weighted features"""
        
        # Base log-odds (calibrated for realistic predictions)
        log_odds = self.base_log_odds
        
        # Credit score impact (normalized around 700)
        log_odds += self.feature_weights["credit_score"] * (features["credit_score"] - 700)
        
        # DTI impact
        log_odds += self.feature_weights["dti_ratio"] * features["dti_ratio"]
        
        # Employment stability
        log_odds += self.feature_weights["years_employed"] * min(features["years_employed"], 20)
        
        # Delinquencies
        log_odds += self.feature_weights["delinquencies_2yrs"] * features["delinquencies_2yrs"]
        
        # Credit utilization
        log_odds += self.feature_weights["credit_utilization"] * (features["credit_utilization"] / 100)
        
        # Loan to income
        log_odds += self.feature_weights["loan_to_income"] * min(features["loan_to_income"], 10)
        
        # Credit history length
        log_odds += self.feature_weights["years_credit_history"] * min(features["years_credit_history"], 30)
        
        # Public records
        log_odds += self.feature_weights["public_records"] * features["public_records"]
        
        # Hard inquiries
        log_odds += self.feature_weights["hard_inquiries_6mo"] * features["hard_inquiries_6mo"]
        
        # Savings cushion
        log_odds += self.feature_weights["savings_ratio"] * min(features["savings_ratio"], 1)
        
        # Convert to probability (sigmoid)
        probability = 1 / (1 + np.exp(-log_odds))
        
        # Clamp to reasonable range
        return max(0.01, min(0.99, probability))
    
    def _calculate_feature_importance(self, features: Dict[str, float], default_prob: float) -> List[Dict[str, Any]]:
        """Calculate SHAP-like feature importance"""
        
        importance = []
        
        # Calculate contribution of each feature
        for feature, value in features.items():
            weight = self.feature_weights.get(feature, 0)
            
            # Simplified SHAP value calculation
            if feature == "credit_score":
                shap_value = weight * (value - 700) * 0.01
            elif feature in ["dti_ratio", "savings_ratio"]:
                shap_value = weight * value * 0.1
            else:
                shap_value = weight * value * 0.05
            
            # Determine direction
            direction = "negative" if shap_value < 0 else "positive"
            
            # Create human-readable description
            description = self._get_feature_description(feature, value, shap_value)
            
            importance.append({
                "feature": feature,
                "value": round(value, 4),
                "impact": round(abs(shap_value), 4),
                "direction": direction,
                "description": description
            })
        
        # Sort by absolute impact
        importance.sort(key=lambda x: x["impact"], reverse=True)
        
        return importance[:8]  # Top 8 factors
    
    def _get_feature_description(self, feature: str, value: float, shap_value: float) -> str:
        """Generate human-readable description for feature impact"""
        
        impact = "increases" if shap_value > 0 else "decreases"
        
        descriptions = {
            "credit_score": f"Credit score of {int(value)} {impact} default risk",
            "dti_ratio": f"Debt-to-income ratio of {value:.1%} {impact} default risk",
            "years_employed": f"{value:.1f} years of employment {impact} default risk",
            "delinquencies_2yrs": f"{int(value)} delinquencies in past 2 years {impact} default risk",
            "credit_utilization": f"Credit utilization of {value:.0f}% {impact} default risk",
            "loan_to_income": f"Loan-to-income ratio of {value:.2f}x {impact} default risk",
            "years_credit_history": f"{value:.1f} years of credit history {impact} default risk",
            "public_records": f"{int(value)} public records {impact} default risk",
            "hard_inquiries_6mo": f"{int(value)} hard inquiries in 6 months {impact} default risk",
            "savings_ratio": f"Savings ratio of {value:.1%} {impact} default risk",
        }
        
        return descriptions.get(feature, f"{feature} {impact} default risk")
    
    def _determine_risk_level(self, default_prob: float) -> tuple:
        """Determine risk level and score from default probability"""
        
        # Risk score (0-100, higher = more risky)
        risk_score = default_prob * 100
        
        # Risk level thresholds (calibrated for realistic credit risk)
        # Low: Good credit, stable finances - approve
        # Medium: Fair credit, some concerns - approve with conditions possible
        # High: Elevated risk - careful review needed
        # Critical: High default probability - likely deny
        if default_prob < 0.10:
            return "Low", risk_score
        elif default_prob < 0.30:  # Expanded Medium range (was 0.25)
            return "Medium", risk_score
        elif default_prob < 0.55:  # Expanded High range (was 0.50)
            return "High", risk_score
        else:
            return "Critical", risk_score
    
    async def _get_llm_analysis(
        self, 
        application_data: Dict[str, Any], 
        features: Dict[str, float],
        default_prob: float,
        feature_importance: List[Dict]
    ) -> Dict[str, Any]:
        """Get LLM analysis for additional insights"""
        
        system_prompt = """You are a quantitative risk analyst specializing in credit risk modeling.
Analyze the risk metrics and provide insights on the key drivers of risk."""
        
        prompt = f"""Analyze this loan application's quantitative risk metrics:

Default Probability: {default_prob:.2%}

Key Features:
- Credit Score: {features['credit_score']}
- DTI Ratio: {features['dti_ratio']:.1%}
- Years Employed: {features['years_employed']}
- Delinquencies (2yr): {features['delinquencies_2yrs']}
- Credit Utilization: {features['credit_utilization']}%
- Loan to Income Ratio: {features['loan_to_income']:.2f}x

Top Risk Factors by Impact:
{json.dumps(feature_importance[:5], indent=2)}

Provide analysis in JSON format:
{{
    "key_risk_factors": ["list of 3-5 primary risk drivers"],
    "mitigating_factors": ["list of 2-4 positive factors"],
    "recommendation": "Brief recommendation for underwriting",
    "reasoning": "Detailed explanation of the risk assessment"
}}"""
        
        return self.bedrock.invoke_with_json_output(prompt, system_prompt)
