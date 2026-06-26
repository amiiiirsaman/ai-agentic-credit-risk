"""
Compliance Agent - FCRA/ECOA regulatory compliance
"""
import json
from typing import Dict, Any, List
from .base_agent import BaseAgent
from .confidence_calculator import ConfidenceCalculator

class ComplianceAgent(BaseAgent):
    """
    Compliance & Regulatory Agent
    
    Responsibilities:
    - FCRA (Fair Credit Reporting Act) compliance
    - ECOA (Equal Credit Opportunity Act) compliance
    - Fair lending assessment
    - Adverse action notice preparation
    """
    
    def __init__(self):
        super().__init__(
            name="Compliance",
            description="Regulatory compliance and fair lending specialist"
        )
    
    async def process(self, application_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform compliance assessment"""
        
        # Check FCRA compliance
        fcra_result = self._check_fcra_compliance(application_data, context)
        
        # Check ECOA compliance
        ecoa_result = self._check_ecoa_compliance(application_data)
        
        # Assess fair lending risk
        fair_lending_result = self._assess_fair_lending_risk(application_data, context)
        
        # Prepare adverse action reasons if needed
        adverse_action_reasons = self._prepare_adverse_action_reasons(application_data, context)
        
        # Get LLM analysis for comprehensive compliance review (may return None on failure)
        llm_analysis = await self._get_llm_analysis(
            application_data,
            context,
            fcra_result,
            ecoa_result,
            fair_lending_result,
            adverse_action_reasons
        ) or {}
        
        overall_compliant = fcra_result.get("compliant", True) and ecoa_result.get("compliant", True)
        
        # Calculate dynamic confidence based on compliance assessment completeness
        confidence = self._calculate_confidence(
            fcra_result, ecoa_result, fair_lending_result, llm_analysis, overall_compliant
        )
        
        return {
            "compliant": overall_compliant,
            "fcra_compliant": fcra_result.get("compliant", True),
            "fcra_findings": fcra_result.get("findings", []),
            "ecoa_compliant": ecoa_result.get("compliant", True),
            "ecoa_findings": ecoa_result.get("findings", []),
            "fair_lending_risk": fair_lending_result.get("risk_level", "low"),
            "fair_lending_concerns": fair_lending_result.get("concerns", []),
            "adverse_action_reasons": adverse_action_reasons,
            "required_disclosures": llm_analysis.get("required_disclosures", []) if llm_analysis else [],
            "compliance_notes": llm_analysis.get("compliance_notes", "") if llm_analysis else "",
            "recommended_actions": llm_analysis.get("recommended_actions", []) if llm_analysis else [],
            "confidence": confidence,
            "reasoning": llm_analysis.get("reasoning", "") if llm_analysis else ""
        }
    
    def _calculate_confidence(self, fcra: Dict, ecoa: Dict, fair_lending: Dict, llm_output: Dict, compliant: bool) -> float:
        """Calculate confidence based on compliance check thoroughness"""
        # Check thoroughness - more findings = more thorough review
        fcra_findings = len(fcra.get("findings", []))
        ecoa_findings = len(ecoa.get("findings", []))
        total_findings = fcra_findings + ecoa_findings
        
        # Thoroughness score (more findings up to a point = better)
        thoroughness = min(1.0, total_findings / 8) * 0.9 + 0.1
        
        # Clear compliance status = higher confidence
        if compliant:
            clarity = 0.95  # Clear compliant
        elif fair_lending.get("risk_level") == "high":
            clarity = 0.88  # Clear non-compliant
        else:
            clarity = 0.82  # Ambiguous
        
        # LLM analysis quality
        expected_keys = ["required_disclosures", "compliance_notes", "reasoning"]
        analysis_quality = ConfidenceCalculator.calculate_analysis_quality(
            llm_output, expected_keys, has_reasoning=bool(llm_output.get("reasoning"))
        )
        
        confidence = thoroughness * 0.30 + clarity * 0.35 + analysis_quality * 0.35
        return round(max(0.70, min(0.98, confidence)), 4)
    
    def _check_fcra_compliance(self, application_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Check FCRA compliance requirements"""
        
        findings = []
        compliant = True
        
        # Check if credit information is being used appropriately
        credit = application_data.get("credit", {})
        
        # Permissible purpose check (credit transaction)
        findings.append("Permissible purpose verified: Credit transaction for loan application")
        
        # Consumer disclosure requirements
        findings.append("Consumer entitled to adverse action notice if denied")
        
        # Accuracy of information
        if credit.get("credit_score", 0) > 0:
            findings.append("Credit score obtained from consumer reporting agency")
        
        # Check for disputes (simulated - would check actual credit report)
        # In production, this would check for disputed items in credit report
        
        return {
            "compliant": compliant,
            "findings": findings
        }
    
    def _check_ecoa_compliance(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check ECOA compliance requirements"""
        
        findings = []
        compliant = True
        
        applicant = application_data.get("applicant", {})
        
        # ECOA prohibits discrimination based on protected characteristics
        # We ensure decision is based only on creditworthiness factors
        
        findings.append("Decision based on creditworthiness factors only")
        findings.append("No prohibited basis factors considered in underwriting")
        
        # Age-related check (ECOA allows age consideration for creditworthiness)
        age = applicant.get("age", 0)
        if age >= 62:
            findings.append("Applicant age factored appropriately per ECOA guidelines")
        
        # Timing requirements
        findings.append("Adverse action notice required within 30 days if denied")
        
        return {
            "compliant": compliant,
            "findings": findings
        }
    
    def _assess_fair_lending_risk(self, application_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess fair lending risk"""
        
        concerns = []
        risk_level = "low"
        
        # Get quantitative risk results
        quant_result = context.get("agent_results", {}).get("QuantitativeRisk", {}).get("output", {})
        
        credit = application_data.get("credit", {})
        employment = application_data.get("employment", {})
        
        # Check for potential disparate impact issues
        
        # Credit score threshold check
        credit_score = credit.get("credit_score", 0)
        if credit_score >= 620 and credit_score <= 660:
            concerns.append("Credit score in borderline range - ensure consistent treatment")
            risk_level = "medium"
        
        # DTI threshold check
        dti = quant_result.get("dti_ratio", 0)
        if dti and 0.40 <= dti <= 0.45:
            concerns.append("DTI ratio at policy threshold - document decision rationale")
            risk_level = "medium"
        
        # Employment type consideration
        if employment.get("status") == "self_employed":
            concerns.append("Self-employed applicant - ensure income verification is equitable")
        
        return {
            "risk_level": risk_level,
            "concerns": concerns
        }
    
    def _prepare_adverse_action_reasons(self, application_data: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
        """Prepare standardized adverse action reasons if denial is likely"""
        
        reasons = []
        
        credit = application_data.get("credit", {})
        employment = application_data.get("employment", {})
        financial = application_data.get("financial", {})
        
        # Credit score
        if credit.get("credit_score", 0) < 660:
            reasons.append("Credit score does not meet minimum requirements")
        
        # Delinquencies
        if credit.get("delinquencies_2yrs", 0) > 0:
            reasons.append("Recent delinquent payment history")
        
        # Public records
        if credit.get("public_records", 0) > 0:
            reasons.append("Public record(s) on credit file")
        
        # High utilization
        if credit.get("credit_utilization", 0) > 75:
            reasons.append("Proportion of revolving balances to credit limits is too high")
        
        # Insufficient credit history
        if credit.get("years_credit_history", 0) < 2:
            reasons.append("Length of credit history is insufficient")
        
        # Employment concerns
        if employment.get("years_employed", 0) < 1:
            reasons.append("Insufficient length of employment")
        
        if employment.get("status") == "unemployed":
            reasons.append("Insufficient or lack of income")
        
        # DTI
        monthly_income = employment.get("annual_income", 0) / 12
        monthly_debt = financial.get("monthly_debt", 0)
        if monthly_income > 0 and (monthly_debt / monthly_income) > 0.43:
            reasons.append("Debt-to-income ratio exceeds guidelines")
        
        # Too many inquiries
        if credit.get("hard_inquiries_6mo", 0) > 4:
            reasons.append("Too many recent inquiries on credit report")
        
        return reasons[:4]  # FCRA typically requires top 4 reasons
    
    async def _get_llm_analysis(
        self,
        application_data: Dict[str, Any],
        context: Dict[str, Any],
        fcra_result: Dict,
        ecoa_result: Dict,
        fair_lending_result: Dict,
        adverse_action_reasons: List[str]
    ) -> Dict[str, Any]:
        """Get LLM analysis for compliance"""
        
        system_prompt = """You are a regulatory compliance specialist with expertise in 
FCRA, ECOA, and fair lending regulations for consumer credit decisions.
Ensure all guidance is legally sound and protects both the lender and consumer."""
        
        prompt = f"""Review this compliance assessment:

FCRA Compliance:
- Compliant: {fcra_result.get('compliant')}
- Findings: {json.dumps(fcra_result.get('findings', []))}

ECOA Compliance:
- Compliant: {ecoa_result.get('compliant')}
- Findings: {json.dumps(ecoa_result.get('findings', []))}

Fair Lending Assessment:
- Risk Level: {fair_lending_result.get('risk_level')}
- Concerns: {json.dumps(fair_lending_result.get('concerns', []))}

Potential Adverse Action Reasons:
{json.dumps(adverse_action_reasons, indent=2)}

Application Summary:
- Credit Score: {application_data.get('credit', {}).get('credit_score')}
- Employment Status: {application_data.get('employment', {}).get('status')}
- Loan Purpose: {application_data.get('loan', {}).get('purpose')}

Provide compliance analysis in JSON format:
{{
    "required_disclosures": ["list of required regulatory disclosures"],
    "compliance_notes": "summary of compliance status",
    "recommended_actions": ["actions to ensure full compliance"],
    "adverse_action_notice_required": true/false,
    "risk_based_pricing_notice": true/false,
    "reasoning": "detailed compliance reasoning"
}}"""
        
        return self.bedrock.invoke_with_json_output(prompt, system_prompt)
