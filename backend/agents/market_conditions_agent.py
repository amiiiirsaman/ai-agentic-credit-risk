"""
Market Conditions Agent - Economic and market risk assessment
"""
import json
from typing import Dict, Any
from datetime import datetime
from .base_agent import BaseAgent
from .confidence_calculator import ConfidenceCalculator

class MarketConditionsAgent(BaseAgent):
    """
    Market Conditions Agent
    
    Responsibilities:
    - Assess current economic conditions
    - Evaluate market risk factors
    - Provide risk adjustments based on macro factors
    - Consider regional economic factors
    """
    
    def __init__(self):
        super().__init__(
            name="MarketConditions",
            description="Economic and market conditions assessment specialist"
        )
        
        # Simulated market data (would be real API data in production)
        self.market_data = {
            "fed_funds_rate": 5.25,
            "unemployment_rate": 3.8,
            "inflation_rate": 3.2,
            "gdp_growth": 2.4,
            "consumer_confidence": 102.5,
            "housing_price_index_yoy": 4.5,
            "mortgage_rate_30yr": 6.85,
            "sp500_ytd": 12.5,
            "yield_curve_spread": 0.15,  # 10yr - 2yr spread
        }
    
    async def process(self, application_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess market conditions impact on loan"""
        
        loan = application_data.get("loan", {})
        loan_purpose = loan.get("purpose", "personal")
        
        # Calculate economic risk factor
        economic_risk = self._calculate_economic_risk()
        
        # Get sector-specific risk
        sector_risk = self._assess_sector_risk(loan_purpose)
        
        # Calculate risk adjustment
        risk_adjustment = self._calculate_risk_adjustment(economic_risk, sector_risk, loan_purpose)
        
        # Get regional factors (simulated)
        regional_factors = self._get_regional_factors()
        
        # Get LLM analysis
        llm_analysis = await self._get_llm_analysis(
            application_data,
            economic_risk,
            sector_risk,
            risk_adjustment,
            regional_factors
        ) or {}
        
        # Calculate dynamic confidence - market analysis has inherent uncertainty
        confidence = self._calculate_confidence(economic_risk, sector_risk, llm_analysis)
        
        return {
            "economic_risk_factor": round(economic_risk, 4),
            "sector_risk": sector_risk,
            "risk_adjustment": round(risk_adjustment, 4),
            "market_conditions_summary": llm_analysis.get("market_summary", "") if llm_analysis else "",
            "economic_indicators": self.market_data,
            "regional_factors": regional_factors,
            "rate_environment": self._assess_rate_environment(),
            "outlook": llm_analysis.get("outlook", "stable") if llm_analysis else "stable",
            "market_concerns": llm_analysis.get("concerns", []) if llm_analysis else [],
            "recommendations": llm_analysis.get("recommendations", []) if llm_analysis else [],
            "confidence": confidence,
            "reasoning": llm_analysis.get("reasoning", "") if llm_analysis else ""
        }
    
    def _calculate_confidence(self, economic_risk: float, sector_risk: str, llm_output: Dict) -> float:
        """Calculate confidence - market conditions have inherent volatility"""
        # Market predictions inherently less certain than data-driven metrics
        base_confidence = 0.72
        
        # More extreme economic conditions = clearer signal
        if economic_risk < 0.3 or economic_risk > 0.7:
            risk_clarity = 0.15
        elif economic_risk < 0.4 or economic_risk > 0.6:
            risk_clarity = 0.08
        else:
            risk_clarity = 0.0
        
        # Sector risk clarity
        sector_bonus = {"low": 0.08, "medium": 0.04, "high": 0.10}.get(sector_risk, 0.05)
        
        expected_keys = ["market_summary", "outlook", "concerns", "reasoning"]
        analysis_quality = ConfidenceCalculator.calculate_analysis_quality(
            llm_output, expected_keys, has_reasoning=bool(llm_output.get("reasoning"))
        ) * 0.15
        
        confidence = base_confidence + risk_clarity + sector_bonus + analysis_quality
        return round(max(0.62, min(0.92, confidence)), 4)
    
    def _calculate_economic_risk(self) -> float:
        """Calculate overall economic risk factor (0-1)"""
        
        risk = 0.5  # Base neutral risk
        
        # Unemployment impact
        unemployment = self.market_data["unemployment_rate"]
        if unemployment > 5.0:
            risk += 0.15
        elif unemployment > 4.0:
            risk += 0.05
        elif unemployment < 3.5:
            risk -= 0.05
        
        # Inflation impact
        inflation = self.market_data["inflation_rate"]
        if inflation > 5.0:
            risk += 0.15
        elif inflation > 3.5:
            risk += 0.05
        elif inflation < 2.5:
            risk -= 0.05
        
        # GDP growth impact
        gdp = self.market_data["gdp_growth"]
        if gdp < 0:
            risk += 0.20  # Recession
        elif gdp < 1.5:
            risk += 0.10
        elif gdp > 3.0:
            risk -= 0.10
        
        # Yield curve (inverted = recession signal)
        yield_spread = self.market_data["yield_curve_spread"]
        if yield_spread < 0:
            risk += 0.15  # Inverted yield curve
        elif yield_spread < 0.25:
            risk += 0.05
        
        # Consumer confidence
        confidence = self.market_data["consumer_confidence"]
        if confidence < 80:
            risk += 0.10
        elif confidence > 100:
            risk -= 0.05
        
        return max(0.1, min(0.9, risk))
    
    def _assess_sector_risk(self, loan_purpose: str) -> str:
        """Assess sector-specific risk"""
        
        housing_growth = self.market_data["housing_price_index_yoy"]
        
        if loan_purpose in ["home_purchase", "refinance"]:
            if housing_growth > 10:
                return "elevated"  # Potential bubble
            elif housing_growth < 0:
                return "high"  # Declining market
            elif housing_growth < 2:
                return "moderate"
            else:
                return "low"
        
        elif loan_purpose == "auto":
            # Auto sector generally follows consumer confidence
            if self.market_data["consumer_confidence"] < 90:
                return "moderate"
            return "low"
        
        elif loan_purpose == "business":
            # Business loans more sensitive to economic cycle
            if self.market_data["gdp_growth"] < 1.5:
                return "elevated"
            return "moderate"
        
        return "moderate"  # Default for other purposes
    
    def _calculate_risk_adjustment(self, economic_risk: float, sector_risk: str, loan_purpose: str) -> float:
        """Calculate rate adjustment based on market conditions"""
        
        # Base adjustment from economic risk
        base_adjustment = (economic_risk - 0.5) * 0.5  # -25 to +20 bps range
        
        # Sector adjustment
        sector_adjustments = {
            "low": -0.125,
            "moderate": 0,
            "elevated": 0.25,
            "high": 0.50
        }
        base_adjustment += sector_adjustments.get(sector_risk, 0)
        
        # Purpose-specific adjustments
        if loan_purpose in ["home_purchase", "refinance"]:
            # Housing loans get slight adjustment based on rate environment
            if self.market_data["mortgage_rate_30yr"] > 7.5:
                base_adjustment += 0.125  # Higher rates = more risk
        
        return base_adjustment
    
    def _assess_rate_environment(self) -> str:
        """Assess current rate environment"""
        
        fed_rate = self.market_data["fed_funds_rate"]
        
        if fed_rate >= 5.0:
            return "restrictive"
        elif fed_rate >= 3.0:
            return "neutral"
        elif fed_rate >= 1.0:
            return "accommodative"
        else:
            return "highly_accommodative"
    
    def _get_regional_factors(self) -> Dict[str, Any]:
        """Get regional economic factors (simulated)"""
        
        return {
            "region": "National Average",
            "local_unemployment": self.market_data["unemployment_rate"] + 0.2,
            "local_housing_trend": "stable",
            "economic_outlook": "moderate growth",
            "major_employers_stable": True
        }
    
    async def _get_llm_analysis(
        self,
        application_data: Dict[str, Any],
        economic_risk: float,
        sector_risk: str,
        risk_adjustment: float,
        regional_factors: Dict
    ) -> Dict[str, Any]:
        """Get LLM analysis for market conditions"""
        
        system_prompt = """You are an economic analyst specializing in credit market conditions 
and their impact on lending decisions. Provide insights on how current market conditions 
affect loan risk and pricing."""
        
        loan = application_data.get("loan", {})
        
        prompt = f"""Analyze market conditions for this loan application:

Loan Details:
- Amount: ${loan.get('amount', 0):,.2f}
- Purpose: {loan.get('purpose')}
- Term: {loan.get('term_months')} months

Current Economic Indicators:
- Federal Funds Rate: {self.market_data['fed_funds_rate']}%
- Unemployment Rate: {self.market_data['unemployment_rate']}%
- Inflation Rate: {self.market_data['inflation_rate']}%
- GDP Growth: {self.market_data['gdp_growth']}%
- Consumer Confidence: {self.market_data['consumer_confidence']}
- 30-Year Mortgage Rate: {self.market_data['mortgage_rate_30yr']}%
- Yield Curve Spread: {self.market_data['yield_curve_spread']}%

Risk Assessment:
- Economic Risk Factor: {economic_risk:.2f}
- Sector Risk: {sector_risk}
- Rate Adjustment: {risk_adjustment:+.2%}

Regional Factors:
{json.dumps(regional_factors, indent=2)}

Provide analysis in JSON format:
{{
    "market_summary": "Brief summary of current market conditions",
    "outlook": "improving" | "stable" | "declining",
    "concerns": ["list market-related concerns for this loan"],
    "recommendations": ["recommendations based on market conditions"],
    "timing_assessment": "assessment of loan timing given current conditions",
    "reasoning": "detailed reasoning for market impact assessment"
}}"""
        
        return self.bedrock.invoke_with_json_output(prompt, system_prompt)
