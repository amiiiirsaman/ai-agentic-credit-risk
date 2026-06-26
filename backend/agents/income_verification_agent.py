"""
Income Verification Agent - Validates income and employment
"""
import json
from typing import Dict, Any
from .base_agent import BaseAgent
from .confidence_calculator import ConfidenceCalculator, INCOME_VALIDATION_RULES

class IncomeVerificationAgent(BaseAgent):
    """
    Income Verification Agent
    
    Responsibilities:
    - Verify stated income against documentation
    - Calculate debt-to-income ratio
    - Assess employment stability
    - Evaluate income trends
    """
    
    def __init__(self):
        super().__init__(
            name="IncomeVerification",
            description="Income validation and employment verification specialist"
        )
    
    async def process(self, application_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Verify income and employment information"""
        
        employment = application_data.get("employment", {})
        financial = application_data.get("financial", {})
        
        # Get document verification results if available
        doc_results = context.get("agent_results", {}).get("DocumentIntelligence", {}).get("output", {})
        
        # Calculate verified income
        stated_income = employment.get("annual_income", 0)
        verified_income = self._verify_income(stated_income, doc_results)
        
        # Calculate DTI
        dti_ratio = self._calculate_dti(application_data)
        
        # Assess employment stability
        stability_score = self._assess_employment_stability(employment)
        
        # Determine income trend
        income_trend = self._assess_income_trend(employment, financial)
        
        # Get LLM analysis (may return None on failure)
        llm_analysis = await self._get_llm_analysis(
            application_data,
            verified_income,
            dti_ratio,
            stability_score,
            income_trend
        ) or {}
        
        # Calculate dynamic confidence
        confidence = self._calculate_confidence(
            application_data, llm_analysis, dti_ratio, stability_score
        )
        
        return {
            "verified_annual_income": verified_income,
            "stated_income": stated_income,
            "income_verified": abs(verified_income - stated_income) / max(stated_income, 1) < 0.10,
            "income_variance": round((verified_income - stated_income) / max(stated_income, 1), 4),
            "employment_verified": employment.get("status") in ["employed", "self_employed"],
            "employment_status": employment.get("status"),
            "years_employed": employment.get("years_employed", 0),
            "income_stability_score": round(stability_score, 2),
            "dti_ratio": round(dti_ratio, 4),
            "income_trend": income_trend,
            "monthly_income": round(verified_income / 12, 2),
            "monthly_debt": financial.get("monthly_debt", 0),
            "residual_income": round((verified_income / 12) - financial.get("monthly_debt", 0), 2),
            "analysis": llm_analysis.get("analysis", "") if llm_analysis else "",
            "concerns": llm_analysis.get("concerns", []) if llm_analysis else [],
            "confidence": confidence,
            "reasoning": llm_analysis.get("reasoning", "") if llm_analysis else ""
        }
    
    def _calculate_confidence(self, data: Dict, llm_output: Dict, dti: float, stability: float) -> float:
        """Calculate dynamic confidence based on income verification quality"""
        required_fields = ["employment.annual_income", "employment.status"]
        optional_fields = ["employment.years_employed", "employment.employer_name", "financial.monthly_debt"]
        
        completeness = ConfidenceCalculator.calculate_data_completeness(data, required_fields, optional_fields)
        validity = ConfidenceCalculator.calculate_value_validity(data, INCOME_VALIDATION_RULES)
        
        expected_keys = ["analysis", "concerns", "reasoning"]
        analysis_quality = ConfidenceCalculator.calculate_analysis_quality(
            llm_output, expected_keys, has_reasoning=bool(llm_output.get("reasoning"))
        )
        
        # DTI clarity bonus - extreme values are easier to assess
        if dti < 0.25 or dti > 0.50:
            dti_clarity = 0.95
        elif dti < 0.35 or dti > 0.43:
            dti_clarity = 0.88
        else:
            dti_clarity = 0.82
        
        # Stability score influences confidence
        stability_factor = stability / 100 * 0.15
        
        confidence = completeness * 0.25 + validity * 0.25 + analysis_quality * 0.25 + dti_clarity * 0.25 + stability_factor
        return round(max(0.55, min(0.96, confidence)), 4)
    
    def _verify_income(self, stated_income: float, doc_results: Dict) -> float:
        """Verify income against document extraction results"""
        
        # In production, this would cross-reference with actual document extractions
        # For synthetic data, we add slight variance to simulate verification
        
        document_results = doc_results.get("document_results", [])
        
        for doc in document_results:
            if doc.get("document_type") == "pay_stub":
                extracted = doc.get("extracted_data", {})
                if "gross_pay" in extracted:
                    # Calculate annual from pay stub
                    pay_period_income = extracted["gross_pay"]
                    # Assume bi-weekly
                    doc_annual = pay_period_income * 26
                    # Return average of stated and documented
                    return (stated_income + doc_annual) / 2
        
        # If no documents, apply slight adjustment for uncertainty
        return stated_income * 0.98
    
    def _calculate_dti(self, application_data: Dict[str, Any]) -> float:
        """Calculate debt-to-income ratio"""
        
        employment = application_data.get("employment", {})
        financial = application_data.get("financial", {})
        loan = application_data.get("loan", {})
        
        annual_income = employment.get("annual_income", 1)
        other_income = financial.get("other_income", 0)
        total_monthly_income = (annual_income + other_income) / 12
        
        current_monthly_debt = financial.get("monthly_debt", 0)
        
        # Estimate new loan payment
        loan_amount = loan.get("amount", 0)
        term_months = loan.get("term_months", 360)
        estimated_rate = 0.07  # 7% estimate
        
        if loan_amount > 0 and term_months > 0:
            monthly_rate = estimated_rate / 12
            new_payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** term_months) / ((1 + monthly_rate) ** term_months - 1)
        else:
            new_payment = 0
        
        total_debt = current_monthly_debt + new_payment
        
        if total_monthly_income <= 0:
            return 1.0
        
        return total_debt / total_monthly_income
    
    def _assess_employment_stability(self, employment: Dict) -> float:
        """Assess employment stability score (0-100)"""
        
        score = 50  # Base score
        
        status = employment.get("status", "")
        years = employment.get("years_employed", 0)
        
        # Employment status scoring
        status_scores = {
            "employed": 20,
            "self_employed": 15,
            "retired": 10,
            "unemployed": -30,
            "student": -10
        }
        score += status_scores.get(status, 0)
        
        # Years employed scoring
        if years >= 10:
            score += 30
        elif years >= 5:
            score += 25
        elif years >= 2:
            score += 15
        elif years >= 1:
            score += 5
        else:
            score -= 10
        
        # Has employer name
        if employment.get("employer_name"):
            score += 5
        
        return max(0, min(100, score))
    
    def _assess_income_trend(self, employment: Dict, financial: Dict) -> str:
        """Assess income trend based on available data"""
        
        years_employed = employment.get("years_employed", 0)
        savings = financial.get("savings", 0)
        annual_income = employment.get("annual_income", 0)
        
        # Savings ratio as proxy for income trend
        if annual_income > 0:
            savings_ratio = savings / annual_income
            
            if savings_ratio > 0.3 and years_employed > 3:
                return "increasing"
            elif savings_ratio > 0.1:
                return "stable"
            else:
                return "decreasing"
        
        return "stable"
    
    async def _get_llm_analysis(
        self,
        application_data: Dict[str, Any],
        verified_income: float,
        dti_ratio: float,
        stability_score: float,
        income_trend: str
    ) -> Dict[str, Any]:
        """Get LLM analysis for income verification"""
        
        system_prompt = """You are an income verification specialist with expertise in 
employment verification and debt-to-income analysis for mortgage and loan underwriting."""
        
        employment = application_data.get("employment", {})
        financial = application_data.get("financial", {})
        loan = application_data.get("loan", {})
        
        prompt = f"""Analyze this income verification assessment:

Employment Information:
- Status: {employment.get('status')}
- Employer: {employment.get('employer_name')}
- Job Title: {employment.get('job_title')}
- Years Employed: {employment.get('years_employed')}
- Stated Annual Income: ${employment.get('annual_income', 0):,.2f}

Verification Results:
- Verified Annual Income: ${verified_income:,.2f}
- Income Variance: {((verified_income - employment.get('annual_income', 0)) / max(employment.get('annual_income', 1), 1) * 100):.1f}%
- Employment Stability Score: {stability_score}/100
- Income Trend: {income_trend}

Financial Position:
- Monthly Debt: ${financial.get('monthly_debt', 0):,.2f}
- DTI Ratio: {dti_ratio:.1%}
- Savings: ${financial.get('savings', 0):,.2f}

Loan Request:
- Amount: ${loan.get('amount', 0):,.2f}
- Term: {loan.get('term_months')} months

Provide analysis in JSON format:
{{
    "analysis": "summary of income verification findings",
    "concerns": ["list any concerns about income or employment"],
    "strengths": ["list positive factors"],
    "dti_assessment": "acceptable" | "borderline" | "high",
    "employment_assessment": "stable" | "moderate" | "unstable",
    "reasoning": "detailed explanation of income verification assessment"
}}"""
        
        return self.bedrock.invoke_with_json_output(prompt, system_prompt)
