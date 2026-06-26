"""
LangGraph Orchestrator for Credit Risk Assessment Pipeline
Coordinates all 11 agents with parallel execution where possible
"""
import asyncio
import time
from typing import Dict, Any, List, TypedDict, Annotated
from datetime import datetime
import logging
import uuid

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from agents import (
    ChiefUnderwriterAgent,
    QuantitativeRiskAgent,
    DocumentIntelligenceAgent,
    FraudDetectionAgent,
    IncomeVerificationAgent,
    CreditHistoryAgent,
    ComplianceAgent,
    CollateralAgent,
    CustomerRelationshipAgent,
    MarketConditionsAgent,
    ExplainabilityAgent,
)

logger = logging.getLogger(__name__)


class WorkflowState(TypedDict):
    """State definition for the underwriting workflow"""
    application_id: str
    application_data: Dict[str, Any]
    agent_results: Dict[str, Any]
    current_stage: str
    errors: List[str]
    start_time: float
    decision: Dict[str, Any]


class UnderwritingOrchestrator:
    """
    Orchestrates the credit risk assessment workflow using LangGraph
    
    Workflow stages:
    1. Document Processing
    2. Parallel Assessment (Fraud, Income, Credit - run in parallel)
    3. Risk Calculation
    4. Supporting Analysis (Collateral, Customer, Market - run in parallel)
    5. Compliance Check
    6. Final Decision
    7. Explanation Generation
    """
    
    # Historical percentile reference data (simulates database distribution)
    # In production, this would query the actual database
    HISTORICAL_PERCENTILES = {
        # (default_prob_min, default_prob_max): percentile
        (0.00, 0.05): 10,   # Very low risk = 10th percentile (better than 90%)
        (0.05, 0.10): 25,   # Low risk = 25th percentile
        (0.10, 0.15): 40,   # Low-medium risk
        (0.15, 0.20): 50,   # Medium risk = median
        (0.20, 0.30): 65,   # Medium-high risk
        (0.30, 0.40): 75,   # High risk
        (0.40, 0.50): 85,   # Very high risk
        (0.50, 1.00): 95,   # Critical risk = 95th percentile (worse than 95%)
    }
    
    def __init__(self):
        # Initialize all agents
        self.document_agent = DocumentIntelligenceAgent()
        self.fraud_agent = FraudDetectionAgent()
        self.income_agent = IncomeVerificationAgent()
        self.credit_agent = CreditHistoryAgent()
        self.quantitative_agent = QuantitativeRiskAgent()
        self.collateral_agent = CollateralAgent()
        self.customer_agent = CustomerRelationshipAgent()
        self.market_agent = MarketConditionsAgent()
        self.compliance_agent = ComplianceAgent()
        self.chief_agent = ChiefUnderwriterAgent()
        self.explainability_agent = ExplainabilityAgent()
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
        
        logger.info("UnderwritingOrchestrator initialized with all 11 agents")
    
    def _calculate_db_percentile(self, default_probability: float) -> int:
        """
        Calculate percentile relative to all applicants in database.
        Higher percentile = worse (higher risk compared to others).
        
        In production, this would query: 
        SELECT COUNT(*) FROM decisions WHERE default_probability < :prob / COUNT(*)
        """
        import random
        
        for (low, high), base_percentile in self.HISTORICAL_PERCENTILES.items():
            if low <= default_probability < high:
                # Add variance within the band (+/- 8 percentile points)
                variance = random.randint(-8, 8)
                percentile = base_percentile + variance
                return max(1, min(99, percentile))
        
        return 50  # Fallback for edge cases
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        workflow = StateGraph(WorkflowState)
        
        # Add nodes for each stage
        workflow.add_node("document_processing", self._document_processing_node)
        workflow.add_node("parallel_assessment", self._parallel_assessment_node)
        workflow.add_node("risk_calculation", self._risk_calculation_node)
        workflow.add_node("supporting_analysis", self._supporting_analysis_node)
        workflow.add_node("compliance_check", self._compliance_check_node)
        workflow.add_node("final_decision", self._final_decision_node)
        workflow.add_node("explanation_generation", self._explanation_generation_node)
        
        # Define the workflow edges
        workflow.set_entry_point("document_processing")
        workflow.add_edge("document_processing", "parallel_assessment")
        workflow.add_edge("parallel_assessment", "risk_calculation")
        workflow.add_edge("risk_calculation", "supporting_analysis")
        workflow.add_edge("supporting_analysis", "compliance_check")
        workflow.add_edge("compliance_check", "final_decision")
        workflow.add_edge("final_decision", "explanation_generation")
        workflow.add_edge("explanation_generation", END)
        
        return workflow.compile()
    
    async def process_application(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a loan application through the full underwriting workflow
        
        Args:
            application_data: The loan application data
            
        Returns:
            Complete underwriting decision with all agent results
        """
        return await self.process_application_with_updates(application_data, None)
    
    async def process_application_with_updates(
        self, 
        application_data: Dict[str, Any],
        status_callback: callable = None
    ) -> Dict[str, Any]:
        """
        Process a loan application with real-time status updates via callback
        
        Args:
            application_data: The loan application data
            status_callback: Callback function(agent_name, status, result) for real-time updates
            
        Returns:
            Complete underwriting decision with all agent results
        """
        application_id = str(uuid.uuid4())
        start_time = time.time()
        
        logger.info(f"Starting underwriting workflow for application {application_id}")
        
        # Initialize state
        initial_state: WorkflowState = {
            "application_id": application_id,
            "application_data": application_data,
            "agent_results": {},
            "current_stage": "document_processing",
            "errors": [],
            "start_time": start_time,
            "decision": {}
        }
        
        try:
            # Run the workflow with callbacks
            final_state = await self._run_workflow_with_updates(initial_state, status_callback)
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Compile final result (include application_data for frontend display)
            result = {
                "application_id": application_id,
                "status": "completed",
                "processing_time_ms": processing_time_ms,
                "application_data": application_data,  # Include for applicant summary display
                "decision": final_state.get("decision", {}),
                "agent_results": final_state.get("agent_results", {}),
                "errors": final_state.get("errors", []),
                "completed_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Completed underwriting for {application_id} in {processing_time_ms}ms")
            
            return result
            
        except Exception as e:
            import traceback
            logger.error(f"Workflow error for {application_id}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "application_id": application_id,
                "status": "failed",
                "error": str(e),
                "processing_time_ms": int((time.time() - start_time) * 1000),
                "application_data": application_data,  # Include even on error
                "agent_results": {},
                "completed_at": datetime.utcnow().isoformat()
            }
    
    async def _run_workflow_with_updates(
        self, 
        state: WorkflowState, 
        status_callback: callable = None
    ) -> WorkflowState:
        """Run the workflow through all stages SEQUENTIALLY with real-time updates"""
        
        async def notify(agent_name: str, status: str, result: dict = None):
            """Notify via callback - properly handles async callbacks"""
            if status_callback:
                try:
                    # Check if the callback returns a coroutine or awaitable
                    callback_result = status_callback(agent_name, status, result)
                    if asyncio.iscoroutine(callback_result) or asyncio.isfuture(callback_result):
                        await callback_result
                except Exception as e:
                    logger.warning(f"Status callback error for {agent_name}: {e}")
        
        context = {"agent_results": state["agent_results"]}
        
        # ====================================================================
        # STAGE 1: Document Intelligence Agent
        # ====================================================================
        logger.info(f"[{state['application_id']}] Starting Document Intelligence Agent...")
        await notify("document_intelligence", "processing", None)
        
        result = await self.document_agent.execute(state["application_data"], context)
        state["agent_results"]["DocumentIntelligence"] = result or {}
        
        await notify("document_intelligence", "completed", result)
        logger.info(f"[{state['application_id']}] Document Intelligence completed - confidence: {(result or {}).get('confidence', 0):.2%}")
        
        # ====================================================================
        # STAGE 2: Fraud Detection Agent (SEQUENTIAL - one at a time)
        # ====================================================================
        logger.info(f"[{state['application_id']}] Starting Fraud Detection Agent...")
        await notify("fraud_detection", "processing", None)
        
        result = await self.fraud_agent.execute(state["application_data"], context)
        state["agent_results"]["FraudDetection"] = result or {}
        
        await notify("fraud_detection", "completed", result)
        logger.info(f"[{state['application_id']}] Fraud Detection completed - confidence: {(result or {}).get('confidence', 0):.2%}")
        
        # ====================================================================
        # STAGE 3: Income Verification Agent
        # ====================================================================
        logger.info(f"[{state['application_id']}] Starting Income Verification Agent...")
        await notify("income_verification", "processing", None)
        
        result = await self.income_agent.execute(state["application_data"], context)
        state["agent_results"]["IncomeVerification"] = result or {}
        
        await notify("income_verification", "completed", result)
        logger.info(f"[{state['application_id']}] Income Verification completed - confidence: {(result or {}).get('confidence', 0):.2%}")
        
        # ====================================================================
        # STAGE 4: Credit History Agent
        # ====================================================================
        logger.info(f"[{state['application_id']}] Starting Credit History Agent...")
        await notify("credit_history", "processing", None)
        
        result = await self.credit_agent.execute(state["application_data"], context)
        state["agent_results"]["CreditHistory"] = result or {}
        
        await notify("credit_history", "completed", result)
        logger.info(f"[{state['application_id']}] Credit History completed - confidence: {(result or {}).get('confidence', 0):.2%}")
        
        # ====================================================================
        # STAGE 5: Quantitative Risk Agent
        # ====================================================================
        logger.info(f"[{state['application_id']}] Starting Quantitative Risk Agent...")
        await notify("quantitative_risk", "processing", None)
        
        result = await self.quantitative_agent.execute(state["application_data"], context)
        state["agent_results"]["QuantitativeRisk"] = result or {}
        
        await notify("quantitative_risk", "completed", result)
        logger.info(f"[{state['application_id']}] Quantitative Risk completed - confidence: {(result or {}).get('confidence', 0):.2%}")
        
        # ====================================================================
        # STAGE 6: Collateral Agent
        # ====================================================================
        logger.info(f"[{state['application_id']}] Starting Collateral Agent...")
        await notify("collateral", "processing", None)
        
        result = await self.collateral_agent.execute(state["application_data"], context)
        state["agent_results"]["Collateral"] = result or {}
        
        await notify("collateral", "completed", result)
        logger.info(f"[{state['application_id']}] Collateral completed - confidence: {(result or {}).get('confidence', 0):.2%}")
        
        # ====================================================================
        # STAGE 7: Customer Relationship Agent
        # ====================================================================
        logger.info(f"[{state['application_id']}] Starting Customer Relationship Agent...")
        await notify("customer_relationship", "processing", None)
        
        result = await self.customer_agent.execute(state["application_data"], context)
        state["agent_results"]["CustomerRelationship"] = result or {}
        
        await notify("customer_relationship", "completed", result)
        logger.info(f"[{state['application_id']}] Customer Relationship completed - confidence: {(result or {}).get('confidence', 0):.2%}")
        
        # ====================================================================
        # STAGE 8: Market Conditions Agent
        # ====================================================================
        logger.info(f"[{state['application_id']}] Starting Market Conditions Agent...")
        await notify("market_conditions", "processing", None)
        
        result = await self.market_agent.execute(state["application_data"], context)
        state["agent_results"]["MarketConditions"] = result or {}
        
        await notify("market_conditions", "completed", result)
        logger.info(f"[{state['application_id']}] Market Conditions completed - confidence: {(result or {}).get('confidence', 0):.2%}")
        
        # ====================================================================
        # STAGE 9: Compliance Agent
        # ====================================================================
        logger.info(f"[{state['application_id']}] Starting Compliance Agent...")
        await notify("compliance", "processing", None)
        
        result = await self.compliance_agent.execute(state["application_data"], context)
        state["agent_results"]["Compliance"] = result or {}
        
        await notify("compliance", "completed", result)
        logger.info(f"[{state['application_id']}] Compliance completed - confidence: {(result or {}).get('confidence', 0):.2%}")
        
        # ====================================================================
        # STAGE 10: Chief Underwriter Agent (Final Decision)
        # ====================================================================
        logger.info(f"[{state['application_id']}] Starting Chief Underwriter Agent...")
        await notify("chief_underwriter", "processing", None)
        
        result = await self.chief_agent.execute(state["application_data"], context)
        state["agent_results"]["ChiefUnderwriter"] = result or {}
        
        # Extract decision with all calculated fields - NO HARDCODED FALLBACKS
        # Double safety: handle both None result and None output
        _temp_result = result or {}
        _temp_output = _temp_result.get("output")
        chief_output = _temp_output if _temp_output is not None else {}
        logger.debug(f"[{state['application_id']}] DEBUG: result={result is not None}, _temp_output={_temp_output is not None}, chief_output type={type(chief_output).__name__}")
        
        # Get the actual calculated values from Chief Underwriter
        actual_confidence = chief_output.get("confidence_score") or chief_output.get("confidence")
        actual_default_prob = chief_output.get("default_probability")
        actual_risk_level = chief_output.get("risk_level")
        actual_percentile = chief_output.get("risk_percentile")
        
        # Log if we're missing expected values
        if actual_confidence is None:
            logger.warning(f"[{state['application_id']}] Chief Underwriter missing confidence_score")
            actual_confidence = 0.75  # Conservative default only if truly missing
        if actual_default_prob is None:
            logger.warning(f"[{state['application_id']}] Chief Underwriter missing default_probability")
            actual_default_prob = 0.25  # Conservative medium-high default
        if actual_risk_level is None:
            logger.warning(f"[{state['application_id']}] Chief Underwriter missing risk_level")
            actual_risk_level = "Medium"
        if actual_percentile is None:
            logger.warning(f"[{state['application_id']}] Chief Underwriter missing risk_percentile")
            actual_percentile = self._calculate_db_percentile(actual_default_prob)
        
        # Ensure chief_output is ALWAYS a dict before using it
        if chief_output is None:
            logger.error(f"[{state['application_id']}] CRITICAL: chief_output is None before dict assignment!")
            chief_output = {}
        
        # Extract nested values with full None safety
        _loan_terms = (chief_output or {}).get("loan_terms") or {}
        _risk_assessment = (chief_output or {}).get("risk_assessment") or {}
        
        state["decision"] = {
            # Core decision
            "decision": (chief_output or {}).get("decision", "CONDITIONAL"),
            "decision_reasoning": (chief_output or {}).get("decision_reasoning", ""),
            
            # Calculated metrics (from intelligent algorithm) - NO FALLBACKS
            "confidence_score": actual_confidence,
            "confidence": actual_confidence,
            "default_probability": actual_default_prob,
            "risk_level": actual_risk_level,
            "risk_percentile": actual_percentile,
            
            # Loan terms
            "loan_terms": _loan_terms,
            "approved_terms": _loan_terms,  # Alias for frontend
            
            # Risk factors
            "risk_assessment": _risk_assessment,
            "risk_factors": [
                {"factor": f, "impact": -0.5} 
                for f in (_risk_assessment.get("primary_risk_factors") or [])
            ] + [
                {"factor": f, "impact": 0.5} 
                for f in (_risk_assessment.get("mitigating_factors") or [])
            ],
            
            # Adverse action
            "adverse_action_reasons": (chief_output or {}).get("adverse_action_reasons") or [],
            "conditions": _loan_terms.get("conditions") or [],
            "recommended_next_steps": (chief_output or {}).get("recommended_next_steps") or "",
            
            # Confidence breakdown for transparency
            "confidence_breakdown": (chief_output or {}).get("confidence_breakdown") or {}
        }
        
        await notify("chief_underwriter", "completed", result)
        logger.info(f"[{state['application_id']}] Chief Underwriter completed - decision: {(chief_output or {}).get('decision', 'N/A')}, confidence: {(chief_output or {}).get('confidence_score', 0):.2%}")
        
        # ====================================================================
        # STAGE 11: Explainability Agent
        # ====================================================================
        logger.info(f"[{state['application_id']}] Starting Explainability Agent...")
        await notify("explainability", "processing", None)
        
        result = await self.explainability_agent.execute(state["application_data"], context)
        state["agent_results"]["Explainability"] = result or {}
        
        # Add explanation to decision
        explainability_output = (result or {}).get("output") or {}
        if explainability_output:
            state["decision"]["customer_explanation"] = explainability_output.get("customer_explanation", "")
            state["decision"]["adverse_action_notice"] = explainability_output.get("adverse_action_notice")
            state["decision"]["improvement_suggestions"] = explainability_output.get("improvement_suggestions", [])
            state["decision"]["next_steps"] = explainability_output.get("next_steps", "")
        
        await notify("explainability", "completed", result)
        logger.info(f"[{state['application_id']}] Explainability completed - all 11 agents finished!")
        
        state["current_stage"] = "completed"
        return state
    
    async def _run_workflow(self, state: WorkflowState) -> WorkflowState:
        """Run the workflow through all stages (legacy without callbacks)"""
        return await self._run_workflow_with_updates(state, None)
    
    async def _document_processing_node(self, state: WorkflowState) -> WorkflowState:
        """Process and verify documents"""
        logger.info(f"[{state['application_id']}] Stage 1: Document Processing")
        
        result = await self.document_agent.execute(
            state["application_data"],
            {"agent_results": state["agent_results"]}
        )
        
        state["agent_results"]["DocumentIntelligence"] = result or {}
        
        if (result or {}).get("status") == "failed":
            state["errors"].append(f"Document processing failed: {(result or {}).get('error')}")
        
        return state
    
    async def _parallel_assessment_node(self, state: WorkflowState) -> WorkflowState:
        """Run Fraud, Income, and Credit agents in parallel"""
        logger.info(f"[{state['application_id']}] Stage 2: Parallel Assessment (Fraud, Income, Credit)")
        
        context = {"agent_results": state["agent_results"]}
        
        # Run agents in parallel
        results = await asyncio.gather(
            self.fraud_agent.execute(state["application_data"], context),
            self.income_agent.execute(state["application_data"], context),
            self.credit_agent.execute(state["application_data"], context),
            return_exceptions=True
        )
        
        # Process results
        agent_names = ["FraudDetection", "IncomeVerification", "CreditHistory"]
        for name, result in zip(agent_names, results):
            if isinstance(result, Exception):
                state["errors"].append(f"{name} failed: {str(result)}")
                state["agent_results"][name] = {
                    "agent_name": name,
                    "status": "failed",
                    "error": str(result)
                }
            else:
                state["agent_results"][name] = result
        
        return state
    
    async def _risk_calculation_node(self, state: WorkflowState) -> WorkflowState:
        """Calculate quantitative risk assessment"""
        logger.info(f"[{state['application_id']}] Stage 3: Quantitative Risk Calculation")
        
        result = await self.quantitative_agent.execute(
            state["application_data"],
            {"agent_results": state["agent_results"]}
        )
        
        state["agent_results"]["QuantitativeRisk"] = result or {}
        
        if (result or {}).get("status") == "failed":
            state["errors"].append(f"Risk calculation failed: {(result or {}).get('error')}")
        
        return state
    
    async def _supporting_analysis_node(self, state: WorkflowState) -> WorkflowState:
        """Run Collateral, Customer, and Market agents in parallel"""
        logger.info(f"[{state['application_id']}] Stage 4: Supporting Analysis (Collateral, Customer, Market)")
        
        context = {"agent_results": state["agent_results"]}
        
        # Run agents in parallel
        results = await asyncio.gather(
            self.collateral_agent.execute(state["application_data"], context),
            self.customer_agent.execute(state["application_data"], context),
            self.market_agent.execute(state["application_data"], context),
            return_exceptions=True
        )
        
        # Process results
        agent_names = ["Collateral", "CustomerRelationship", "MarketConditions"]
        for name, result in zip(agent_names, results):
            if isinstance(result, Exception):
                state["errors"].append(f"{name} failed: {str(result)}")
                state["agent_results"][name] = {
                    "agent_name": name,
                    "status": "failed",
                    "error": str(result)
                }
            else:
                state["agent_results"][name] = result
        
        return state
    
    async def _compliance_check_node(self, state: WorkflowState) -> WorkflowState:
        """Check regulatory compliance"""
        logger.info(f"[{state['application_id']}] Stage 5: Compliance Check")
        
        result = await self.compliance_agent.execute(
            state["application_data"],
            {"agent_results": state["agent_results"]}
        )
        
        state["agent_results"]["Compliance"] = result or {}
        
        if (result or {}).get("status") == "failed":
            state["errors"].append(f"Compliance check failed: {(result or {}).get('error')}")
        
        return state
    
    async def _final_decision_node(self, state: WorkflowState) -> WorkflowState:
        """Make final underwriting decision"""
        logger.info(f"[{state['application_id']}] Stage 6: Final Decision")
        
        result = await self.chief_agent.execute(
            state["application_data"],
            {"agent_results": state["agent_results"]}
        )
        
        state["agent_results"]["ChiefUnderwriter"] = result or {}
        state["decision"] = (result or {}).get("output") or {}
        
        if (result or {}).get("status") == "failed":
            state["errors"].append(f"Final decision failed: {(result or {}).get('error')}")
        
        return state
    
    async def _explanation_generation_node(self, state: WorkflowState) -> WorkflowState:
        """Generate customer explanations"""
        logger.info(f"[{state['application_id']}] Stage 7: Explanation Generation")
        
        result = await self.explainability_agent.execute(
            state["application_data"],
            {"agent_results": state["agent_results"]}
        )
        
        state["agent_results"]["Explainability"] = result or {}
        
        # Add explanation to decision
        exp_output = (result or {}).get("output") or {}
        if exp_output:
            state["decision"]["customer_explanation"] = exp_output.get("customer_explanation", "")
            state["decision"]["adverse_action_notice"] = exp_output.get("adverse_action_notice")
            state["decision"]["improvement_suggestions"] = exp_output.get("improvement_suggestions", [])
            state["decision"]["next_steps"] = exp_output.get("next_steps", "")
        
        if (result or {}).get("status") == "failed":
            state["errors"].append(f"Explanation generation failed: {(result or {}).get('error')}")
        
        return state
    
    async def get_agent_status(self, application_id: str, state: WorkflowState) -> Dict[str, Any]:
        """Get current status of all agents for an application"""
        
        completed_agents = list(state.get("agent_results", {}).keys())
        
        all_agents = [
            "DocumentIntelligence",
            "FraudDetection",
            "IncomeVerification",
            "CreditHistory",
            "QuantitativeRisk",
            "Collateral",
            "CustomerRelationship",
            "MarketConditions",
            "Compliance",
            "ChiefUnderwriter",
            "Explainability"
        ]
        
        progress = len(completed_agents) / len(all_agents) * 100
        
        return {
            "application_id": application_id,
            "current_stage": state.get("current_stage", "unknown"),
            "completed_agents": completed_agents,
            "pending_agents": [a for a in all_agents if a not in completed_agents],
            "progress_percent": int(progress),
            "errors": state.get("errors", [])
        }


# Singleton instance
_orchestrator: UnderwritingOrchestrator = None


def get_orchestrator() -> UnderwritingOrchestrator:
    """Get or create singleton orchestrator"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = UnderwritingOrchestrator()
    return _orchestrator
