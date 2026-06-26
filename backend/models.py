"""
Pydantic models for the Credit Risk Assessment Platform
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
import uuid


class LoanPurpose(str, Enum):
    HOME_PURCHASE = "home_purchase"
    REFINANCE = "refinance"
    DEBT_CONSOLIDATION = "debt_consolidation"
    BUSINESS = "business"
    PERSONAL = "personal"
    AUTO = "auto"
    EDUCATION = "education"
    OTHER = "other"


class EmploymentStatus(str, Enum):
    EMPLOYED = "employed"
    SELF_EMPLOYED = "self_employed"
    RETIRED = "retired"
    UNEMPLOYED = "unemployed"
    STUDENT = "student"


class HomeOwnership(str, Enum):
    OWN = "own"
    MORTGAGE = "mortgage"
    RENT = "rent"
    OTHER = "other"


class ApplicationStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    APPROVED = "approved"
    DENIED = "denied"
    CONDITIONAL = "conditional"


class DecisionType(str, Enum):
    APPROVE = "APPROVE"
    DENY = "DENY"
    CONDITIONAL = "CONDITIONAL"


class RiskLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


# Request Models
class ApplicantInfo(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(..., pattern=r'^\+?1?\d{9,15}$')
    age: int = Field(..., ge=18, le=120)
    ssn_last_four: Optional[str] = Field(None, pattern=r'^\d{4}$')


class LoanDetails(BaseModel):
    amount: float = Field(..., ge=1000, le=10000000)
    purpose: LoanPurpose
    term_months: int = Field(..., ge=6, le=360)
    collateral_type: Optional[str] = None
    collateral_value: Optional[float] = None


class EmploymentInfo(BaseModel):
    status: EmploymentStatus
    employer_name: Optional[str] = None
    job_title: Optional[str] = None
    years_employed: float = Field(..., ge=0, le=60)
    annual_income: float = Field(..., ge=0)
    monthly_income: Optional[float] = None


class CreditInfo(BaseModel):
    credit_score: int = Field(..., ge=300, le=850)
    years_credit_history: float = Field(..., ge=0, le=80)
    num_credit_lines: int = Field(..., ge=0)
    credit_utilization: float = Field(..., ge=0, le=100)
    delinquencies_2yrs: int = Field(default=0, ge=0)
    public_records: int = Field(default=0, ge=0)
    hard_inquiries_6mo: int = Field(default=0, ge=0)


class FinancialInfo(BaseModel):
    monthly_debt: float = Field(..., ge=0)
    savings: float = Field(default=0, ge=0)
    checking_balance: float = Field(default=0, ge=0)
    investment_accounts: float = Field(default=0, ge=0)
    other_income: float = Field(default=0, ge=0)


class DocumentInfo(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    document_type: str  # pay_stub, tax_return, bank_statement, id_document
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    verified: bool = False
    verification_status: Optional[str] = None


class LoanApplicationRequest(BaseModel):
    applicant: ApplicantInfo
    loan: LoanDetails
    employment: EmploymentInfo
    credit: CreditInfo
    financial: FinancialInfo
    documents: List[DocumentInfo] = []

    class Config:
        json_schema_extra = {
            "example": {
                "applicant": {
                    "name": "John Smith",
                    "email": "john.smith@email.com",
                    "phone": "+15551234567",
                    "age": 35,
                    "ssn_last_four": "1234"
                },
                "loan": {
                    "amount": 250000,
                    "purpose": "home_purchase",
                    "term_months": 360,
                    "collateral_type": "real_estate",
                    "collateral_value": 300000
                },
                "employment": {
                    "status": "employed",
                    "employer_name": "Tech Corp Inc",
                    "job_title": "Software Engineer",
                    "years_employed": 5.5,
                    "annual_income": 120000
                },
                "credit": {
                    "credit_score": 720,
                    "years_credit_history": 12,
                    "num_credit_lines": 5,
                    "credit_utilization": 25,
                    "delinquencies_2yrs": 0,
                    "public_records": 0,
                    "hard_inquiries_6mo": 1
                },
                "financial": {
                    "monthly_debt": 1500,
                    "savings": 50000,
                    "checking_balance": 15000,
                    "investment_accounts": 100000
                }
            }
        }


# Response Models
class RiskFactor(BaseModel):
    feature: str
    impact: float  # SHAP value
    direction: str  # "positive" or "negative"
    description: str


class AgentResult(BaseModel):
    agent_name: str
    status: str  # "completed", "failed", "skipped"
    processing_time_ms: int
    confidence: float
    output: Dict[str, Any]
    reasoning: Optional[str] = None


class DocumentVerificationResult(BaseModel):
    document_id: str
    document_type: str
    verified: bool
    confidence: float
    extracted_data: Dict[str, Any]
    fraud_indicators: List[str] = []
    fraud_risk_score: float = 0.0


class QuantitativeRiskResult(BaseModel):
    default_probability: float = Field(..., ge=0, le=1)
    risk_level: RiskLevel
    risk_score: float = Field(..., ge=0, le=100)
    feature_importance: List[RiskFactor]
    model_confidence: float


class ComplianceResult(BaseModel):
    compliant: bool
    fcra_compliant: bool
    ecoa_compliant: bool
    fair_lending_risk: str  # "low", "medium", "high"
    adverse_action_reasons: List[str] = []
    required_disclosures: List[str] = []


class FraudDetectionResult(BaseModel):
    fraud_risk_score: float = Field(..., ge=0, le=100)
    risk_level: str  # "low", "medium", "high", "critical"
    fraud_indicators: List[str] = []
    synthetic_identity_score: float = 0.0
    velocity_check_passed: bool = True


class IncomeVerificationResult(BaseModel):
    verified_annual_income: float
    income_stability_score: float
    employment_verified: bool
    dti_ratio: float
    income_trend: str  # "increasing", "stable", "decreasing"


class CreditAnalysisResult(BaseModel):
    credit_quality: str  # "excellent", "good", "fair", "poor"
    payment_behavior_prediction: str
    credit_trajectory: str  # "improving", "stable", "declining"
    key_findings: List[str]


class CollateralResult(BaseModel):
    estimated_value: float
    valuation_confidence: float
    ltv_ratio: float
    collateral_quality: str  # "excellent", "good", "fair", "poor"


class CustomerValueResult(BaseModel):
    lifetime_value_score: float
    relationship_strength: str
    retention_risk: str
    pricing_recommendation: str


class MarketConditionsResult(BaseModel):
    economic_risk_factor: float
    market_conditions_summary: str
    risk_adjustment: float
    regional_factors: Dict[str, Any]


class ExplanationResult(BaseModel):
    customer_explanation: str
    adverse_action_notice: Optional[str] = None
    improvement_suggestions: List[str]
    next_steps: str
    plain_language_summary: str


class LoanTerms(BaseModel):
    approved_amount: float
    interest_rate: float
    term_months: int
    monthly_payment: float
    total_interest: float
    conditions: List[str] = []


class UnderwritingDecision(BaseModel):
    application_id: str
    decision: DecisionType
    confidence: float = Field(..., ge=0, le=1)
    
    # Risk Assessment
    default_probability: float = Field(..., ge=0, le=1)
    risk_level: RiskLevel
    risk_factors: List[RiskFactor]
    
    # Agent Results
    agent_results: Dict[str, AgentResult]
    
    # Approved Terms (if applicable)
    loan_terms: Optional[LoanTerms] = None
    
    # Explanations
    decision_reasoning: str
    customer_explanation: str
    adverse_action_notice: Optional[str] = None
    improvement_suggestions: List[str] = []
    next_steps: str
    
    # Metadata
    processing_time_ms: int
    decided_at: datetime = Field(default_factory=datetime.utcnow)
    decided_by: str = "AI Underwriting System"


class LoanApplicationResponse(BaseModel):
    application_id: str
    status: ApplicationStatus
    submitted_at: datetime
    message: str


class ApplicationStatusResponse(BaseModel):
    application_id: str
    status: ApplicationStatus
    current_agent: Optional[str] = None
    agents_completed: List[str] = []
    progress_percent: int = 0
    estimated_completion_seconds: Optional[int] = None


# Agent Status Models
class AgentHealth(BaseModel):
    agent_name: str
    status: str  # "healthy", "degraded", "unhealthy"
    last_check: datetime
    avg_response_time_ms: int
    success_rate: float


class SystemHealth(BaseModel):
    status: str
    agents: List[AgentHealth]
    database_connected: bool
    aws_bedrock_connected: bool
    uptime_seconds: int


# Analytics Models
class DashboardMetrics(BaseModel):
    total_applications: int
    approved_count: int
    denied_count: int
    conditional_count: int
    pending_count: int
    approval_rate: float
    avg_processing_time_ms: int
    avg_default_probability: float
    total_loan_volume: float


class PerformanceMetrics(BaseModel):
    model_accuracy: float
    precision: float
    recall: float
    f1_score: float
    auc_roc: float
    avg_prediction_time_ms: int
