"""
Base Agent class for all Credit Risk Assessment agents
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import logging
import time
import uuid

from .bedrock_client import get_bedrock_client, BedrockClient


logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all agents in the credit risk system"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.bedrock: BedrockClient = get_bedrock_client()
        self.logger = logging.getLogger(f"agent.{name}")
    
    @abstractmethod
    async def process(self, application_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the application data and return agent results
        
        Args:
            application_data: The loan application data
            context: Additional context including results from other agents
            
        Returns:
            Agent processing results
        """
        pass
    
    async def execute(self, application_data: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute the agent with timing and error handling
        
        Args:
            application_data: The loan application data
            context: Additional context
            
        Returns:
            Wrapped agent result with metadata
        """
        context = context or {}
        execution_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        self.logger.info(f"[{execution_id}] Starting {self.name} agent")
        
        try:
            result = await self.process(application_data, context)
            
            # Ensure result is a dict - agents can return None on error
            if result is None:
                result = {}
                self.logger.warning(f"[{execution_id}] {self.name} process() returned None, using empty dict")
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Extract confidence - check multiple keys (agents may use different names)
            confidence = (
                result.get("confidence") or 
                result.get("confidence_score") or 
                result.get("model_confidence") or
                0.75  # Conservative fallback only if truly missing
            )
            
            wrapped_result = {
                "agent_name": self.name,
                "status": "completed",
                "processing_time_ms": processing_time_ms,
                "confidence": confidence,
                "confidence_score": confidence,  # Alias for compatibility
                "output": result,
                "reasoning": result.get("reasoning"),
                "execution_id": execution_id,
                "completed_at": datetime.utcnow().isoformat()
            }
            
            self.logger.info(f"[{execution_id}] {self.name} completed in {processing_time_ms}ms")
            
            return wrapped_result
            
        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            error_result = {
                "agent_name": self.name,
                "status": "failed",
                "processing_time_ms": processing_time_ms,
                "confidence": 0.0,
                "output": {},
                "error": str(e),
                "execution_id": execution_id,
                "completed_at": datetime.utcnow().isoformat()
            }
            
            self.logger.error(f"[{execution_id}] {self.name} failed: {str(e)}")
            
            return error_result
    
    def _format_application_summary(self, application_data: Dict[str, Any]) -> str:
        """Format application data for LLM prompts"""
        applicant = application_data.get("applicant", {})
        loan = application_data.get("loan", {})
        employment = application_data.get("employment", {})
        credit = application_data.get("credit", {})
        financial = application_data.get("financial", {})
        
        summary = f"""
APPLICANT INFORMATION:
- Name: {applicant.get('name', 'N/A')}
- Age: {applicant.get('age', 'N/A')}

LOAN REQUEST:
- Amount: ${loan.get('amount', 0):,.2f}
- Purpose: {loan.get('purpose', 'N/A')}
- Term: {loan.get('term_months', 0)} months
- Collateral Type: {loan.get('collateral_type', 'None')}
- Collateral Value: {f"${loan.get('collateral_value'):,.2f}" if loan.get('collateral_value') else 'N/A'}

EMPLOYMENT:
- Status: {employment.get('status', 'N/A')}
- Employer: {employment.get('employer_name', 'N/A')}
- Job Title: {employment.get('job_title', 'N/A')}
- Years Employed: {employment.get('years_employed', 0)}
- Annual Income: ${employment.get('annual_income', 0):,.2f}

CREDIT PROFILE:
- Credit Score: {credit.get('credit_score', 0)}
- Years of Credit History: {credit.get('years_credit_history', 0)}
- Number of Credit Lines: {credit.get('num_credit_lines', 0)}
- Credit Utilization: {credit.get('credit_utilization', 0)}%
- Delinquencies (2 years): {credit.get('delinquencies_2yrs', 0)}
- Public Records: {credit.get('public_records', 0)}
- Hard Inquiries (6 months): {credit.get('hard_inquiries_6mo', 0)}

FINANCIAL POSITION:
- Monthly Debt: ${financial.get('monthly_debt', 0):,.2f}
- Savings: ${financial.get('savings', 0):,.2f}
- Checking Balance: ${financial.get('checking_balance', 0):,.2f}
- Investment Accounts: ${financial.get('investment_accounts', 0):,.2f}
- Other Income: ${financial.get('other_income', 0):,.2f}
"""
        return summary
    
    def _calculate_dti(self, application_data: Dict[str, Any]) -> float:
        """Calculate Debt-to-Income ratio"""
        employment = application_data.get("employment", {})
        financial = application_data.get("financial", {})
        
        annual_income = employment.get("annual_income", 0)
        other_income = financial.get("other_income", 0)
        monthly_income = (annual_income + other_income) / 12
        
        monthly_debt = financial.get("monthly_debt", 0)
        
        if monthly_income <= 0:
            return 1.0  # 100% DTI if no income
        
        return round(monthly_debt / monthly_income, 4)
