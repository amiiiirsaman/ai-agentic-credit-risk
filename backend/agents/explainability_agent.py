"""
Explainability Agent - Customer communication and explanation generation
"""
import json
from typing import Dict, Any, List
from .base_agent import BaseAgent
from .confidence_calculator import ConfidenceCalculator

class ExplainabilityAgent(BaseAgent):
    """
    Explainability & Communication Agent
    
    Responsibilities:
    - Generate plain-language explanations of decisions
    - Create adverse action notices (if denied)
    - Provide improvement recommendations
    - Communicate next steps to applicants
    """
    
    def __init__(self):
        super().__init__(
            name="Explainability",
            description="Customer communication and decision explanation specialist"
        )
    
    async def process(self, application_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate customer-facing explanations and communications"""
        
        # Get the chief underwriter's decision
        chief_result = context.get("agent_results", {}).get("ChiefUnderwriter", {}).get("output", {})
        decision = chief_result.get("decision", "PENDING")
        
        # Get compliance adverse action reasons
        compliance_result = context.get("agent_results", {}).get("Compliance", {}).get("output", {})
        adverse_reasons = compliance_result.get("adverse_action_reasons", [])
        
        # Get risk factors
        quant_result = context.get("agent_results", {}).get("QuantitativeRisk", {}).get("output", {})
        
        # Generate plain language explanation (may return None on failure)
        explanation = await self._generate_explanation(
            application_data,
            decision,
            chief_result,
            quant_result
        ) or {}
        
        # Generate adverse action notice if needed
        adverse_notice = None
        if decision == "DENY":
            adverse_notice = await self._generate_adverse_action_notice(
                application_data,
                adverse_reasons,
                chief_result
            )
        
        # Generate improvement suggestions (may return empty list on failure)
        improvements = await self._generate_improvement_suggestions(
            application_data,
            decision,
            quant_result,
            compliance_result
        ) or []
        
        # Generate next steps
        next_steps = self._generate_next_steps(decision, chief_result)
        
        # Calculate dynamic confidence - explanation quality depends on available context
        confidence = self._calculate_confidence(explanation, improvements, decision)
        
        return {
            "customer_explanation": explanation.get("explanation", "") if explanation else "",
            "plain_language_summary": explanation.get("summary", "") if explanation else "",
            "decision_factors": explanation.get("decision_factors", []) if explanation else [],
            "adverse_action_notice": adverse_notice,
            "improvement_suggestions": improvements if improvements else [],
            "next_steps": next_steps,
            "faq": self._generate_faq(decision),
            "contact_information": self._get_contact_info(),
            "confidence": confidence,
            "reasoning": explanation.get("reasoning", "") if explanation else ""
        }
    
    def _calculate_confidence(self, explanation: Dict, improvements: List, decision: str) -> float:
        """Calculate confidence based on explanation completeness"""
        # Explanation quality
        has_explanation = bool(explanation.get("explanation"))
        has_summary = bool(explanation.get("summary"))
        has_factors = len(explanation.get("decision_factors", [])) > 0
        has_improvements = len(improvements) > 0
        
        completeness = (has_explanation * 0.35 + has_summary * 0.25 + 
                       has_factors * 0.25 + has_improvements * 0.15)
        
        # Clear decisions get better explanations
        if decision in ["APPROVE", "DENY"]:
            clarity = 0.95
        else:  # CONDITIONAL
            clarity = 0.88
        
        confidence = completeness * 0.60 + clarity * 0.40
        return round(max(0.70, min(0.98, confidence)), 4)
    
    async def _generate_explanation(
        self,
        application_data: Dict[str, Any],
        decision: str,
        chief_result: Dict,
        quant_result: Dict
    ) -> Dict[str, Any]:
        """Generate plain-language explanation of the decision"""
        
        system_prompt = """You are a customer communication specialist who explains 
complex financial decisions in clear, empathetic, and professional language.
Your explanations should be understandable to someone without financial expertise.
Be honest but supportive, especially for denials."""
        
        applicant = application_data.get("applicant", {})
        loan = application_data.get("loan", {})
        
        # Safely extract loan terms with None handling
        loan_terms = chief_result.get('loan_terms') or {}
        approved_amount = loan_terms.get('approved_amount')
        interest_rate = loan_terms.get('interest_rate')
        term_months = loan_terms.get('term_months')
        conditions = loan_terms.get('conditions', [])
        
        prompt = f"""Generate a customer-friendly explanation for this loan decision:

Applicant: {applicant.get('name')}
Loan Request: ${loan.get('amount') or 0:,.2f} for {loan.get('purpose')}

Decision: {decision}

Decision Reasoning (from underwriter):
{chief_result.get('decision_reasoning', 'No reasoning provided')}

Risk Assessment:
- Default Probability: {quant_result.get('default_probability', 'N/A')}
- Risk Level: {quant_result.get('risk_level', 'N/A')}

If APPROVE:
- Approved Amount: {f"${approved_amount:,.2f}" if approved_amount else 'N/A'}
- Interest Rate: {f"{interest_rate:.2%}" if interest_rate else 'N/A'}
- Term: {term_months if term_months else 'N/A'} months

If CONDITIONAL:
- Conditions: {conditions}

If DENY:
- Primary Reasons: {chief_result.get('adverse_action_reasons', [])}

Generate a response in JSON format:
{{
    "explanation": "Full customer-facing explanation (2-3 paragraphs, warm and professional)",
    "summary": "One sentence summary of the decision",
    "decision_factors": ["list of key factors that influenced the decision, explained simply"],
    "tone_check": "Confirm the tone is appropriate: empathetic for denials, congratulatory for approvals",
    "reasoning": "Why this explanation was crafted this way"
}}"""
        
        return self.bedrock.invoke_with_json_output(prompt, system_prompt)
    
    async def _generate_adverse_action_notice(
        self,
        application_data: Dict[str, Any],
        adverse_reasons: List[str],
        chief_result: Dict
    ) -> str:
        """Generate FCRA-compliant adverse action notice"""
        
        system_prompt = """You are a compliance specialist who creates legally compliant 
adverse action notices. The notice must be clear, professional, and include all 
FCRA-required elements."""
        
        applicant = application_data.get("applicant", {})
        loan = application_data.get("loan", {})
        
        # Use top 4 reasons as required by FCRA
        top_reasons = adverse_reasons[:4] if adverse_reasons else ["Unable to verify information"]
        
        prompt = f"""Generate an FCRA-compliant adverse action notice:

Applicant: {applicant.get('name')}
Application: ${loan.get('amount') or 0:,.2f} {loan.get('purpose')} loan

Reasons for Denial (use these exact reasons):
{json.dumps(top_reasons, indent=2)}

The notice must include:
1. Statement of adverse action taken
2. Name and address of consumer reporting agency (use: "National Credit Bureau, PO Box 12345, Anytown, ST 12345")
3. Statement that the CRA did not make the decision
4. Consumer's right to obtain free credit report within 60 days
5. Consumer's right to dispute information
6. The specific reasons for the denial (from above)

Generate a professional, compliant adverse action notice letter.
Return ONLY the letter text, no JSON."""
        
        response = self.bedrock.invoke(prompt, system_prompt)
        return response
    
    async def _generate_improvement_suggestions(
        self,
        application_data: Dict[str, Any],
        decision: str,
        quant_result: Dict,
        compliance_result: Dict
    ) -> List[str]:
        """Generate actionable improvement suggestions"""
        
        credit = application_data.get("credit", {})
        financial = application_data.get("financial", {})
        employment = application_data.get("employment", {})
        
        suggestions = []
        
        # Credit score suggestions
        if credit.get("credit_score", 0) < 700:
            suggestions.append("Consider improving your credit score by paying all bills on time and reducing credit card balances")
        
        # Credit utilization
        if credit.get("credit_utilization", 0) > 30:
            suggestions.append(f"Reduce your credit utilization from {credit.get('credit_utilization')}% to below 30% by paying down credit card balances")
        
        # Delinquencies
        if credit.get("delinquencies_2yrs", 0) > 0:
            suggestions.append("Maintain on-time payments for all accounts to build a stronger payment history")
        
        # Savings
        annual_income = employment.get("annual_income", 0)
        savings = financial.get("savings", 0)
        if annual_income > 0 and savings < annual_income * 0.1:
            suggestions.append("Build your savings to demonstrate financial stability - aim for at least 3-6 months of expenses")
        
        # Employment stability
        if employment.get("years_employed", 0) < 2:
            suggestions.append("Longer employment history strengthens your application - consider waiting until you have 2+ years at your current job")
        
        # DTI
        monthly_income = annual_income / 12
        monthly_debt = financial.get("monthly_debt", 0)
        if monthly_income > 0 and (monthly_debt / monthly_income) > 0.35:
            suggestions.append("Reduce your monthly debt obligations to improve your debt-to-income ratio")
        
        # Add conditional approval suggestions
        if decision == "CONDITIONAL":
            suggestions.append("Complete any requested documentation promptly to finalize your approval")
        
        # If denied, add re-application guidance
        if decision == "DENY":
            suggestions.append("You may reapply after addressing the factors mentioned in your adverse action notice")
            suggestions.append("Consider consulting with a HUD-approved housing counselor for free guidance")
        
        return suggestions[:6]  # Return top 6 suggestions
    
    def _generate_next_steps(self, decision: str, chief_result: Dict) -> str:
        """Generate next steps based on decision"""
        
        if decision == "APPROVE":
            return """Congratulations on your approval! Here are your next steps:
1. Review your loan terms carefully
2. You will receive closing documents within 3-5 business days
3. Sign and return all required documents
4. Funds will be disbursed according to your loan type
5. Contact us if you have any questions"""
        
        elif decision == "CONDITIONAL":
            conditions = chief_result.get("loan_terms", {}).get("conditions", [])
            conditions_text = "\n".join([f"  - {c}" for c in conditions]) if conditions else "  - See attached requirements"
            return f"""Your application has been conditionally approved! To finalize:
1. Please provide the following:
{conditions_text}
2. Submit all documents within 30 days
3. Once received, final review typically takes 2-3 business days
4. Contact your loan officer if you have questions about any requirements"""
        
        else:  # DENY
            return """We understand this is not the news you were hoping for. Here's what you can do:
1. Review the adverse action notice for specific reasons
2. Obtain your free credit report to check for errors
3. Work on the improvement suggestions provided
4. You may reapply after 6 months or once you've addressed the concerns
5. Consider speaking with a financial counselor for personalized guidance"""
    
    def _generate_faq(self, decision: str) -> List[Dict[str, str]]:
        """Generate relevant FAQ based on decision"""
        
        common_faq = [
            {
                "question": "How long is this decision valid?",
                "answer": "This decision is valid for 90 days from the date of this letter."
            },
            {
                "question": "Who can I contact with questions?",
                "answer": "You can reach our loan support team at 1-800-XXX-XXXX or email loans@example.com"
            }
        ]
        
        if decision == "APPROVE":
            common_faq.extend([
                {
                    "question": "Can I change my loan terms?",
                    "answer": "Some terms may be adjustable before closing. Contact your loan officer to discuss options."
                },
                {
                    "question": "What happens at closing?",
                    "answer": "You'll sign final documents, pay any closing costs, and receive your funds according to your loan type."
                }
            ])
        
        elif decision == "DENY":
            common_faq.extend([
                {
                    "question": "Can I appeal this decision?",
                    "answer": "If you believe there's an error, you can submit additional documentation for reconsideration within 30 days."
                },
                {
                    "question": "How soon can I reapply?",
                    "answer": "You may reapply at any time, but we recommend waiting at least 6 months after addressing the reasons for denial."
                }
            ])
        
        return common_faq
    
    def _get_contact_info(self) -> Dict[str, str]:
        """Get contact information for customer support"""
        return {
            "phone": "1-800-XXX-XXXX",
            "email": "loans@example.com",
            "hours": "Monday-Friday 8am-8pm EST",
            "website": "www.example.com/loans"
        }
