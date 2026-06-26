"""
Collateral Valuation Agent - Asset valuation for secured loans
"""
import json
from typing import Dict, Any
from .base_agent import BaseAgent


class CollateralAgent(BaseAgent):
    """
    Collateral Valuation Agent
    
    Responsibilities:
    - Assess collateral value
    - Calculate loan-to-value ratio
    - Evaluate collateral quality
    - Risk adjustment for secured loans
    """
    
    def __init__(self):
        super().__init__(
            name="Collateral",
            description="Collateral valuation and LTV analysis specialist"
        )
    
    async def process(self, application_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess collateral for secured loans"""
        
        loan = application_data.get("loan", {})
        
        collateral_type = loan.get("collateral_type")
        stated_value = loan.get("collateral_value", 0)
        loan_amount = loan.get("amount", 0)
        
        # If no collateral, return minimal assessment
        if not collateral_type or stated_value <= 0:
            return {
                "has_collateral": False,
                "estimated_value": 0,
                "valuation_confidence": 0,
                "ltv_ratio": 1.0,  # 100% LTV (unsecured)
                "collateral_quality": "N/A",
                "collateral_type": "unsecured",
                "risk_adjustment": 0,
                "valuation_notes": "Unsecured loan - no collateral assessment required",
                "confidence": 1.0,
                "reasoning": "No collateral provided for this loan application"
            }
        
        # Assess collateral value
        estimated_value, valuation_confidence = self._estimate_value(collateral_type, stated_value)
        
        # Calculate LTV
        ltv_ratio = loan_amount / estimated_value if estimated_value > 0 else 1.0
        
        # Assess collateral quality
        quality = self._assess_quality(collateral_type, ltv_ratio, valuation_confidence)
        
        # Calculate risk adjustment
        risk_adjustment = self._calculate_risk_adjustment(quality, ltv_ratio)
        
        # Get LLM analysis (may return None on failure)
        llm_analysis = await self._get_llm_analysis(
            application_data,
            estimated_value,
            valuation_confidence,
            ltv_ratio,
            quality
        ) or {}
        
        return {
            "has_collateral": True,
            "collateral_type": collateral_type,
            "stated_value": stated_value,
            "estimated_value": round(estimated_value, 2),
            "valuation_confidence": round(valuation_confidence, 4),
            "ltv_ratio": round(ltv_ratio, 4),
            "ltv_percent": round(ltv_ratio * 100, 2),
            "collateral_quality": quality,
            "risk_adjustment": round(risk_adjustment, 4),
            "valuation_notes": llm_analysis.get("valuation_notes", "") if llm_analysis else "",
            "concerns": llm_analysis.get("concerns", []) if llm_analysis else [],
            "recommendations": llm_analysis.get("recommendations", []) if llm_analysis else [],
            "confidence": valuation_confidence,
            "reasoning": llm_analysis.get("reasoning", "") if llm_analysis else ""
        }
    
    def _estimate_value(self, collateral_type: str, stated_value: float) -> tuple:
        """Estimate collateral value and confidence"""
        
        # In production, this would integrate with AVM, appraisal services, etc.
        # For synthetic data, apply type-based adjustments
        
        value_adjustments = {
            "real_estate": (0.95, 0.90),  # 95% of stated value, 90% confidence
            "vehicle": (0.85, 0.85),  # Vehicles depreciate, lower confidence
            "securities": (0.98, 0.95),  # Liquid securities are easier to value
            "equipment": (0.70, 0.75),  # Business equipment has lower resale value
            "inventory": (0.50, 0.65),  # Inventory is hardest to liquidate
            "other": (0.75, 0.70),
        }
        
        adjustment, confidence = value_adjustments.get(collateral_type.lower(), (0.80, 0.70))
        
        estimated_value = stated_value * adjustment
        
        return estimated_value, confidence
    
    def _assess_quality(self, collateral_type: str, ltv_ratio: float, valuation_confidence: float) -> str:
        """Assess overall collateral quality"""
        
        # Start with base quality from type
        type_quality = {
            "real_estate": 90,
            "securities": 85,
            "vehicle": 70,
            "equipment": 60,
            "inventory": 50,
            "other": 55,
        }
        
        score = type_quality.get(collateral_type.lower(), 50)
        
        # Adjust for LTV
        if ltv_ratio <= 0.60:
            score += 10
        elif ltv_ratio <= 0.80:
            score += 5
        elif ltv_ratio > 0.95:
            score -= 15
        elif ltv_ratio > 0.90:
            score -= 10
        
        # Adjust for valuation confidence
        score += (valuation_confidence - 0.80) * 20
        
        # Determine quality level
        if score >= 85:
            return "excellent"
        elif score >= 70:
            return "good"
        elif score >= 55:
            return "fair"
        else:
            return "poor"
    
    def _calculate_risk_adjustment(self, quality: str, ltv_ratio: float) -> float:
        """Calculate risk adjustment factor for interest rate"""
        
        # Base adjustment by quality
        quality_adjustments = {
            "excellent": -0.25,  # 25 bps reduction
            "good": 0.0,
            "fair": 0.25,
            "poor": 0.50,
        }
        
        base_adjustment = quality_adjustments.get(quality, 0.25)
        
        # LTV adjustment
        if ltv_ratio > 0.90:
            base_adjustment += 0.25
        elif ltv_ratio > 0.80:
            base_adjustment += 0.125
        elif ltv_ratio <= 0.60:
            base_adjustment -= 0.125
        
        return base_adjustment
    
    async def _get_llm_analysis(
        self,
        application_data: Dict[str, Any],
        estimated_value: float,
        valuation_confidence: float,
        ltv_ratio: float,
        quality: str
    ) -> Dict[str, Any]:
        """Get LLM analysis for collateral"""
        
        system_prompt = """You are a collateral valuation specialist with expertise in 
real estate, vehicles, securities, and business assets valuation for lending purposes."""
        
        loan = application_data.get("loan", {})
        
        prompt = f"""Analyze this collateral assessment:

Loan Details:
- Loan Amount: ${loan.get('amount', 0):,.2f}
- Loan Purpose: {loan.get('purpose')}
- Loan Term: {loan.get('term_months')} months

Collateral Information:
- Type: {loan.get('collateral_type')}
- Stated Value: ${loan.get('collateral_value', 0):,.2f}
- Estimated Value: ${estimated_value:,.2f}
- Valuation Confidence: {valuation_confidence:.0%}
- LTV Ratio: {ltv_ratio:.1%}
- Quality Assessment: {quality}

Provide analysis in JSON format:
{{
    "valuation_notes": "summary of valuation assessment",
    "concerns": ["list any concerns about the collateral"],
    "recommendations": ["recommendations regarding collateral"],
    "additional_requirements": ["any additional appraisal or documentation needed"],
    "ltv_assessment": "acceptable" | "borderline" | "high",
    "reasoning": "detailed reasoning for collateral assessment"
}}"""
        
        return self.bedrock.invoke_with_json_output(prompt, system_prompt)
