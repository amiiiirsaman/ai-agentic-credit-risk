"""
Chief Underwriter Agent - Final decision authority
Aggregates all agent outputs and makes the final underwriting decision
Uses intelligent weighted scoring algorithm for confidence and risk calculations
"""
import json
from typing import Dict, Any, Tuple
from .base_agent import BaseAgent


# Agent weights for confidence aggregation (must sum to 1.0)
AGENT_WEIGHTS = {
    "QuantitativeRisk": 0.25,    # 25% - Core risk assessment
    "FraudDetection": 0.20,      # 20% - Critical for fraud prevention
    "CreditHistory": 0.20,       # 20% - Historical payment behavior
    "IncomeVerification": 0.15,  # 15% - Ability to repay
    "Compliance": 0.10,          # 10% - Regulatory requirements
    "Collateral": 0.05,          # 5% - Security coverage
    "MarketConditions": 0.05,    # 5% - External factors
}

# Risk level thresholds based on default probability
RISK_THRESHOLDS = {
    "Low": (0, 0.10),           # 0-10% default probability
    "Medium": (0.10, 0.25),     # 10-25% default probability
    "High": (0.25, 0.50),       # 25-50% default probability
    "Critical": (0.50, 1.0),    # 50%+ default probability
}


class ChiefUnderwriterAgent(BaseAgent):
    """
    Chief Underwriting Agent - The final decision maker
    
    Responsibilities:
    - Aggregate all agent results using weighted scoring
    - Calculate intelligent confidence scores
    - Make final APPROVE/DENY/CONDITIONAL decision
    - Set loan terms if approved
    - Calculate interest rate based on risk
    """
    
    def __init__(self):
        super().__init__(
            name="ChiefUnderwriter",
            description="Final decision authority that aggregates all agent outputs and makes underwriting decisions"
        )
    
    def _calculate_weighted_confidence(self, agent_results: Dict[str, Any]) -> float:
        """
        Calculate overall confidence using weighted average of agent confidences
        
        Formula: Σ(agent_weight × agent_confidence) for all agents
        """
        total_confidence = 0.0
        total_weight = 0.0
        
        for agent_name, weight in AGENT_WEIGHTS.items():
            agent_data = agent_results.get(agent_name, {})
            # Get confidence from either top level or output
            confidence = agent_data.get("confidence", agent_data.get("output", {}).get("confidence", 0.75))
            
            # Ensure confidence is a valid number
            if isinstance(confidence, (int, float)) and 0 <= confidence <= 1:
                total_confidence += weight * confidence
                total_weight += weight
        
        # Normalize if not all agents contributed
        if total_weight > 0:
            return round(total_confidence / total_weight, 4)
        return 0.75  # Default fallback
    
    def _calculate_risk_metrics(self, agent_results: Dict[str, Any]) -> Tuple[float, str, int]:
        """
        Calculate comprehensive risk metrics from agent results
        
        Returns: (default_probability, risk_level, risk_percentile)
        """
        quant_risk = agent_results.get("QuantitativeRisk", {}).get("output", {})
        fraud_result = agent_results.get("FraudDetection", {}).get("output", {})
        credit_result = agent_results.get("CreditHistory", {}).get("output", {})
        income_result = agent_results.get("IncomeVerification", {}).get("output", {})
        
        # Base default probability from quantitative model
        base_default_prob = quant_risk.get("default_probability", 0.15)
        
        # Adjustments based on other agents
        adjustments = 0.0
        
        # Fraud adjustment (+/- up to 10%)
        fraud_score = fraud_result.get("fraud_risk_score", 20) / 100
        if fraud_score > 0.5:
            adjustments += (fraud_score - 0.5) * 0.20  # High fraud adds up to 10%
        elif fraud_score < 0.2:
            adjustments -= 0.03  # Low fraud reduces by 3%
        
        # Credit history adjustment (+/- up to 8%)
        credit_quality = credit_result.get("credit_quality", "fair")
        credit_adjustments = {
            "excellent": -0.05,
            "good": -0.02,
            "fair": 0.0,
            "poor": 0.05,
            "very_poor": 0.08
        }
        adjustments += credit_adjustments.get(credit_quality, 0)
        
        # Income stability adjustment (+/- up to 5%)
        income_stability = income_result.get("income_stability_score", 50) / 100
        if income_stability > 0.7:
            adjustments -= 0.03
        elif income_stability < 0.4:
            adjustments += 0.05
        
        # DTI ratio adjustment (+/- up to 7%)
        dti = income_result.get("dti_ratio", 0.35)
        if dti > 0.50:
            adjustments += 0.07
        elif dti > 0.43:
            adjustments += 0.04
        elif dti < 0.30:
            adjustments -= 0.02
        
        # Final default probability (clamped to 0.01-0.95)
        final_default_prob = max(0.01, min(0.95, base_default_prob + adjustments))
        
        # Determine risk level
        risk_level = "Medium"  # Default
        for level, (low, high) in RISK_THRESHOLDS.items():
            if low <= final_default_prob < high:
                risk_level = level
                break
        
        # Calculate percentile within risk class (synthetic for now)
        # This represents where this application falls within its risk class
        risk_percentile = self._calculate_risk_percentile(final_default_prob, risk_level)
        
        return round(final_default_prob, 4), risk_level, risk_percentile
    
    def _calculate_risk_percentile(self, default_prob: float, risk_level: str) -> int:
        """
        Calculate percentile within the risk class
        Higher percentile = higher risk within that class
        """
        low, high = RISK_THRESHOLDS.get(risk_level, (0, 1))
        if high == low:
            return 50
        
        # Position within the risk band (0-1)
        position = (default_prob - low) / (high - low)
        
        # Convert to percentile (0-100)
        return max(1, min(99, int(position * 100)))
    
    def _calculate_interest_rate(self, default_prob: float, risk_level: str, loan_term: int) -> float:
        """
        Calculate interest rate based on risk
        
        Base rate + risk premium + term adjustment
        """
        # Base prime rate
        base_rate = 0.055  # 5.5% base
        
        # Risk premium based on default probability
        # Linear scaling: 0% default = 0% premium, 50% default = 15% premium
        risk_premium = default_prob * 0.30
        
        # Term adjustment (longer terms = slightly higher rate)
        if loan_term > 48:
            term_adjustment = 0.005
        elif loan_term > 36:
            term_adjustment = 0.0025
        else:
            term_adjustment = 0
        
        # Risk level caps
        max_rates = {
            "Low": 0.12,
            "Medium": 0.18,
            "High": 0.24,
            "Critical": 0.30
        }
        
        calculated_rate = base_rate + risk_premium + term_adjustment
        max_rate = max_rates.get(risk_level, 0.24)
        
        return round(min(calculated_rate, max_rate), 4)
    
    async def process(self, application_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Make final underwriting decision based on all agent results"""
        
        # Extract results from other agents
        agent_results = context.get("agent_results", {})
        loan = application_data.get("loan", {})
        
        # ===== INTELLIGENT CALCULATIONS =====
        
        # 1. Calculate weighted confidence score
        weighted_confidence = self._calculate_weighted_confidence(agent_results)
        
        # 2. Calculate risk metrics
        default_probability, risk_level, risk_percentile = self._calculate_risk_metrics(agent_results)
        
        # 3. Calculate interest rate
        loan_term = loan.get("term_months", 36)
        calculated_rate = self._calculate_interest_rate(default_probability, risk_level, loan_term)
        
        # Ensure calculated values have defaults BEFORE prompt construction
        weighted_confidence = weighted_confidence if weighted_confidence is not None else 0.75
        default_probability = default_probability if default_probability is not None else 0.25
        risk_level = risk_level if risk_level is not None else "Medium"
        risk_percentile = risk_percentile if risk_percentile is not None else 50
        calculated_rate = calculated_rate if calculated_rate is not None else 0.08
        loan_term = loan_term if loan_term is not None else 36
        
        # Get key metrics from agents for LLM context - use empty dict if None
        quant_risk = agent_results.get("QuantitativeRisk", {}).get("output") or {}
        fraud_result = agent_results.get("FraudDetection", {}).get("output") or {}
        compliance_result = agent_results.get("Compliance", {}).get("output") or {}
        income_result = agent_results.get("IncomeVerification", {}).get("output") or {}
        credit_result = agent_results.get("CreditHistory", {}).get("output") or {}
        collateral_result = agent_results.get("Collateral", {}).get("output") or {}
        market_result = agent_results.get("MarketConditions", {}).get("output") or {}
        
        # Helper to safely format numbers that might be None or non-numeric
        def safe_money(val, default=0):
            try:
                num = float(val) if val is not None else default
                return f"${num:,.2f}"
            except (ValueError, TypeError):
                return f"${default:,.2f}"
        
        def safe_val(val, default='N/A'):
            return val if val is not None else default
        
        def safe_pct(val, default=0.0):
            """Safely format a percentage value"""
            try:
                num = float(val) if val is not None else default
                return f"{num:.2%}"
            except (ValueError, TypeError):
                return f"{default:.2%}"
        
        # Prepare summary for LLM
        application_summary = self._format_application_summary(application_data)
        
        agent_summary = f"""
AGENT ANALYSIS RESULTS:

1. QUANTITATIVE RISK ASSESSMENT:
- Default Probability: {safe_val(quant_risk.get('default_probability'))}
- Risk Level: {safe_val(quant_risk.get('risk_level'))}
- Risk Score: {safe_val(quant_risk.get('risk_score'))}/100
- Model Confidence: {safe_val(quant_risk.get('model_confidence'))}

2. FRAUD DETECTION:
- Fraud Risk Score: {safe_val(fraud_result.get('fraud_risk_score'))}/100
- Risk Level: {safe_val(fraud_result.get('risk_level'))}
- Fraud Indicators: {fraud_result.get('fraud_indicators', [])}
- Synthetic Identity Score: {safe_val(fraud_result.get('synthetic_identity_score'))}

3. COMPLIANCE CHECK:
- Compliant: {safe_val(compliance_result.get('compliant'))}
- FCRA Compliant: {safe_val(compliance_result.get('fcra_compliant'))}
- ECOA Compliant: {safe_val(compliance_result.get('ecoa_compliant'))}
- Fair Lending Risk: {safe_val(compliance_result.get('fair_lending_risk'))}

4. INCOME VERIFICATION:
- Verified Annual Income: {safe_money(income_result.get('verified_annual_income'))}
- Income Stability Score: {safe_val(income_result.get('income_stability_score'))}
- Employment Verified: {safe_val(income_result.get('employment_verified'))}
- DTI Ratio: {safe_val(income_result.get('dti_ratio'))}

5. CREDIT ANALYSIS:
- Credit Quality: {safe_val(credit_result.get('credit_quality'))}
- Payment Behavior Prediction: {safe_val(credit_result.get('payment_behavior_prediction'))}
- Credit Trajectory: {safe_val(credit_result.get('credit_trajectory'))}

6. COLLATERAL ASSESSMENT:
- Estimated Value: {safe_money(collateral_result.get('estimated_value'))}
- LTV Ratio: {safe_val(collateral_result.get('ltv_ratio'))}
- Collateral Quality: {safe_val(collateral_result.get('collateral_quality'))}

7. MARKET CONDITIONS:
- Economic Risk Factor: {safe_val(market_result.get('economic_risk_factor'))}
- Risk Adjustment: {safe_val(market_result.get('risk_adjustment'))}
"""
        
        system_prompt = """You are the Chief Underwriting Officer for a major financial institution.
You have extensive experience in credit risk assessment and loan decisioning.
Your decisions must be fair, compliant with FCRA/ECOA regulations, and based on sound underwriting principles.

You must make a final decision: APPROVE, DENY, or CONDITIONAL.
If approving, you must specify loan terms including interest rate and any conditions.
Your reasoning must be clear and defensible."""
        
        prompt = f"""Based on all agent analyses, make the final underwriting decision.

{application_summary}

{agent_summary}

CALCULATED RISK METRICS (from intelligent scoring algorithm):
- Weighted Confidence Score: {safe_pct(weighted_confidence, 0.75)}
- Calculated Default Probability: {safe_pct(default_probability, 0.25)}
- Risk Level: {risk_level or 'Medium'}
- Risk Percentile (within {risk_level or 'Medium'} class): {risk_percentile or 50}th percentile
- Suggested Interest Rate: {safe_pct(calculated_rate, 0.08)}

Use these calculated metrics to inform your decision. The confidence and risk metrics have been computed
using a weighted algorithm across all agent assessments.

Provide your decision in the following JSON format:
{{
    "decision": "APPROVE" | "DENY" | "CONDITIONAL",
    "decision_reasoning": "Detailed explanation of your decision",
    "loan_terms": {{
        "approved_amount": number or null,
        "interest_rate": {calculated_rate} (use this calculated rate),
        "term_months": {loan_term},
        "monthly_payment": number or null,
        "conditions": ["list of conditions if CONDITIONAL"]
    }},
    "primary_risk_factors": ["list of main risk factors"],
    "mitigating_factors": ["list of positive factors"],
    "adverse_action_reasons": ["list of reasons if DENY or CONDITIONAL"],
    "recommended_next_steps": "What the applicant should do next"
}}"""
        
        llm_result = self.bedrock.invoke_with_json_output(prompt, system_prompt, temperature=0.2) or {}
        
        # Build final result with calculated metrics
        result = {
            # Calculated metrics (not LLM-generated)
            "confidence_score": weighted_confidence,
            "confidence": weighted_confidence,  # Alias for compatibility
            "default_probability": default_probability,
            "risk_level": risk_level,
            "risk_percentile": risk_percentile,
            
            # LLM-generated decision (with safe defaults)
            "decision": llm_result.get("decision", "CONDITIONAL") if llm_result else "CONDITIONAL",
            "decision_reasoning": llm_result.get("decision_reasoning", "Decision pending review") if llm_result else "Decision pending review",
            "reasoning": llm_result.get("decision_reasoning", "") if llm_result else "",
            
            # Loan terms
            "loan_terms": llm_result.get("loan_terms", {
                "approved_amount": None,
                "interest_rate": calculated_rate,
                "term_months": loan_term,
                "monthly_payment": None,
                "conditions": []
            }) if llm_result else {
                "approved_amount": None,
                "interest_rate": calculated_rate,
                "term_months": loan_term,
                "monthly_payment": None,
                "conditions": []
            },
            
            # Risk assessment
            "risk_assessment": {
                "overall_risk_level": risk_level,
                "default_probability": default_probability,
                "risk_percentile": risk_percentile,
                "primary_risk_factors": llm_result.get("primary_risk_factors", []) if llm_result else [],
                "mitigating_factors": llm_result.get("mitigating_factors", []) if llm_result else []
            },
            
            # For adverse action notices
            "adverse_action_reasons": llm_result.get("adverse_action_reasons", []) if llm_result else [],
            "recommended_next_steps": llm_result.get("recommended_next_steps", "") if llm_result else "",
            
            # Agent confidence breakdown for transparency
            "confidence_breakdown": {
                agent: {
                    "weight": f"{weight:.0%}",
                    "confidence": agent_results.get(agent, {}).get("confidence", 0.75)
                }
                for agent, weight in AGENT_WEIGHTS.items()
            }
        }
        
        # Ensure loan terms include calculated rate
        if result["loan_terms"]:
            result["loan_terms"]["interest_rate"] = calculated_rate
        
        # Calculate monthly payment if approved
        if result["decision"] == "APPROVE" and result["loan_terms"]:
            loan_amount = result["loan_terms"].get("approved_amount") or loan.get("amount", 0)
            if loan_amount > 0:
                monthly_rate = calculated_rate / 12
                term = result["loan_terms"].get("term_months", loan_term)
                if monthly_rate > 0:
                    payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** term) / ((1 + monthly_rate) ** term - 1)
                    result["loan_terms"]["monthly_payment"] = round(payment, 2)
                    result["loan_terms"]["approved_amount"] = loan_amount
        
        return result
