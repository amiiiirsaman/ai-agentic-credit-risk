"""
Agents package for Credit Risk Assessment Platform
"""
from .base_agent import BaseAgent
from .bedrock_client import BedrockClient
from .chief_underwriter_agent import ChiefUnderwriterAgent
from .quantitative_risk_agent import QuantitativeRiskAgent
from .document_intelligence_agent import DocumentIntelligenceAgent
from .fraud_detection_agent import FraudDetectionAgent
from .income_verification_agent import IncomeVerificationAgent
from .credit_history_agent import CreditHistoryAgent
from .compliance_agent import ComplianceAgent
from .collateral_agent import CollateralAgent
from .customer_relationship_agent import CustomerRelationshipAgent
from .market_conditions_agent import MarketConditionsAgent
from .explainability_agent import ExplainabilityAgent

__all__ = [
    "BaseAgent",
    "BedrockClient",
    "ChiefUnderwriterAgent",
    "QuantitativeRiskAgent",
    "DocumentIntelligenceAgent",
    "FraudDetectionAgent",
    "IncomeVerificationAgent",
    "CreditHistoryAgent",
    "ComplianceAgent",
    "CollateralAgent",
    "CustomerRelationshipAgent",
    "MarketConditionsAgent",
    "ExplainabilityAgent",
]
