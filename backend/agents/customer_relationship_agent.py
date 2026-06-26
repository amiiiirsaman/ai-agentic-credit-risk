"""
Customer Relationship Agent - Customer lifetime value assessment
"""
import json
from typing import Dict, Any
from .base_agent import BaseAgent
from .confidence_calculator import ConfidenceCalculator

class CustomerRelationshipAgent(BaseAgent):
    """
    Customer Relationship Agent
    
    Responsibilities:
    - Assess customer lifetime value
    - Evaluate relationship strength
    - Determine retention risk
    - Provide pricing recommendations
    """
    
    def __init__(self):
        super().__init__(
            name="CustomerRelationship",
            description="Customer value and relationship assessment specialist"
        )
    
    async def process(self, application_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess customer relationship value"""
        
        # Calculate customer value metrics
        ltv_score = self._calculate_ltv_score(application_data)
        relationship_strength = self._assess_relationship_strength(application_data)
        retention_risk = self._assess_retention_risk(application_data, context)
        pricing_recommendation = self._generate_pricing_recommendation(application_data, ltv_score, context)
        
        # Get LLM analysis (may return None on failure)
        llm_analysis = await self._get_llm_analysis(
            application_data,
            ltv_score,
            relationship_strength,
            retention_risk,
            pricing_recommendation
        ) or {}
        
        # Calculate dynamic confidence
        confidence = self._calculate_confidence(application_data, llm_analysis, ltv_score)
        
        return {
            "lifetime_value_score": round(ltv_score, 2),
            "relationship_strength": relationship_strength,
            "retention_risk": retention_risk,
            "pricing_recommendation": pricing_recommendation,
            "cross_sell_opportunities": llm_analysis.get("cross_sell_opportunities", []) if llm_analysis else [],
            "relationship_notes": llm_analysis.get("relationship_notes", "") if llm_analysis else "",
            "customer_segment": self._determine_segment(ltv_score, relationship_strength),
            "recommended_treatment": llm_analysis.get("recommended_treatment", "standard") if llm_analysis else "standard",
            "confidence": confidence,
            "reasoning": llm_analysis.get("reasoning", "") if llm_analysis else ""
        }
    
    def _calculate_confidence(self, data: Dict, llm_output: Dict, ltv_score: float) -> float:
        """Calculate confidence based on data completeness and LTV clarity"""
        required_fields = ["employment.annual_income", "credit.credit_score"]
        optional_fields = ["financial.savings", "financial.investment_accounts"]
        
        completeness = ConfidenceCalculator.calculate_data_completeness(data, required_fields, optional_fields)
        
        expected_keys = ["cross_sell_opportunities", "relationship_notes", "reasoning"]
        analysis_quality = ConfidenceCalculator.calculate_analysis_quality(
            llm_output, expected_keys, has_reasoning=bool(llm_output.get("reasoning"))
        )
        
        # LTV extremes are clearer
        if ltv_score < 30 or ltv_score > 75:
            clarity = 0.90
        else:
            clarity = 0.78
        
        confidence = completeness * 0.30 + analysis_quality * 0.35 + clarity * 0.35
        return round(max(0.55, min(0.94, confidence)), 4)
    
    def _calculate_ltv_score(self, application_data: Dict[str, Any]) -> float:
        """Calculate customer lifetime value score (0-100)"""
        
        score = 50  # Base score
        
        employment = application_data.get("employment", {})
        financial = application_data.get("financial", {})
        credit = application_data.get("credit", {})
        loan = application_data.get("loan", {})
        
        annual_income = employment.get("annual_income", 0)
        
        # Income-based scoring
        if annual_income >= 200000:
            score += 25
        elif annual_income >= 100000:
            score += 15
        elif annual_income >= 75000:
            score += 10
        elif annual_income < 40000:
            score -= 10
        
        # Asset-based scoring
        total_assets = (
            financial.get("savings", 0) + 
            financial.get("checking_balance", 0) + 
            financial.get("investment_accounts", 0)
        )
        
        if total_assets >= 500000:
            score += 20
        elif total_assets >= 100000:
            score += 10
        elif total_assets >= 50000:
            score += 5
        
        # Credit quality scoring
        credit_score = credit.get("credit_score", 0)
        if credit_score >= 750:
            score += 10
        elif credit_score >= 700:
            score += 5
        elif credit_score < 650:
            score -= 10
        
        # Loan size consideration
        loan_amount = loan.get("amount", 0)
        if loan_amount >= 500000:
            score += 10
        elif loan_amount >= 250000:
            score += 5
        
        return max(0, min(100, score))
    
    def _assess_relationship_strength(self, application_data: Dict[str, Any]) -> str:
        """Assess strength of customer relationship"""
        
        # For new customers, assess potential relationship strength
        employment = application_data.get("employment", {})
        credit = application_data.get("credit", {})
        
        strength_score = 0
        
        # Stability indicators
        if employment.get("years_employed", 0) >= 5:
            strength_score += 2
        elif employment.get("years_employed", 0) >= 2:
            strength_score += 1
        
        # Credit history length
        if credit.get("years_credit_history", 0) >= 10:
            strength_score += 2
        elif credit.get("years_credit_history", 0) >= 5:
            strength_score += 1
        
        # Payment reliability
        if credit.get("delinquencies_2yrs", 0) == 0:
            strength_score += 2
        
        # Employment stability
        if employment.get("status") in ["employed", "retired"]:
            strength_score += 1
        
        if strength_score >= 6:
            return "strong"
        elif strength_score >= 3:
            return "moderate"
        else:
            return "developing"
    
    def _assess_retention_risk(self, application_data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Assess risk of customer attrition"""
        
        credit = application_data.get("credit", {})
        
        # High inquiries suggest shopping around
        inquiries = credit.get("hard_inquiries_6mo", 0)
        
        if inquiries >= 5:
            return "high"
        elif inquiries >= 3:
            return "medium"
        else:
            return "low"
    
    def _generate_pricing_recommendation(
        self,
        application_data: Dict[str, Any],
        ltv_score: float,
        context: Dict[str, Any]
    ) -> str:
        """Generate pricing recommendation based on customer value"""
        
        quant_result = context.get("agent_results", {}).get("QuantitativeRisk", {}).get("output", {})
        risk_level = quant_result.get("risk_level", "Medium")
        
        # High-value, low-risk customers get competitive rates
        if ltv_score >= 75 and risk_level == "Low":
            return "premium_discount"
        
        # Good customers get standard competitive rates
        if ltv_score >= 50 and risk_level in ["Low", "Medium"]:
            return "competitive"
        
        # Riskier customers need risk-adjusted pricing
        if risk_level in ["High", "Critical"]:
            return "risk_adjusted"
        
        return "standard"
    
    def _determine_segment(self, ltv_score: float, relationship_strength: str) -> str:
        """Determine customer segment"""
        
        if ltv_score >= 80:
            return "premium"
        elif ltv_score >= 60 and relationship_strength in ["strong", "moderate"]:
            return "preferred"
        elif ltv_score >= 40:
            return "standard"
        else:
            return "developing"
    
    async def _get_llm_analysis(
        self,
        application_data: Dict[str, Any],
        ltv_score: float,
        relationship_strength: str,
        retention_risk: str,
        pricing_recommendation: str
    ) -> Dict[str, Any]:
        """Get LLM analysis for customer relationship"""
        
        system_prompt = """You are a customer relationship manager with expertise in 
customer lifetime value analysis, retention strategies, and cross-selling financial products."""
        
        employment = application_data.get("employment", {})
        financial = application_data.get("financial", {})
        loan = application_data.get("loan", {})
        
        prompt = f"""Analyze this customer relationship assessment:

Customer Profile:
- Annual Income: ${employment.get('annual_income', 0):,.2f}
- Employment: {employment.get('job_title', 'N/A')} at {employment.get('employer_name', 'N/A')}
- Years Employed: {employment.get('years_employed', 0)}
- Total Assets: ${financial.get('savings', 0) + financial.get('investment_accounts', 0):,.2f}

Loan Request:
- Amount: ${loan.get('amount', 0):,.2f}
- Purpose: {loan.get('purpose')}

Relationship Metrics:
- Lifetime Value Score: {ltv_score}/100
- Relationship Strength: {relationship_strength}
- Retention Risk: {retention_risk}
- Pricing Recommendation: {pricing_recommendation}

Provide analysis in JSON format:
{{
    "cross_sell_opportunities": ["list potential products/services"],
    "relationship_notes": "summary of relationship assessment",
    "recommended_treatment": "premium" | "preferred" | "standard",
    "engagement_strategy": "recommended approach for this customer",
    "reasoning": "detailed reasoning for customer value assessment"
}}"""
        
        return self.bedrock.invoke_with_json_output(prompt, system_prompt)
