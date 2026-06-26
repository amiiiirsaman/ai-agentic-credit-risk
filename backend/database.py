"""
Database models and configuration using SQLAlchemy
"""
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, JSON, 
    Enum as SQLEnum, ForeignKey, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv
import uuid

load_dotenv()

Base = declarative_base()

# Use SQLite for local development
USE_SQLITE = os.getenv("USE_SQLITE", "true").lower() == "true"

if USE_SQLITE:
    # SQLite configuration
    SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), "credit_risk.db")
    DATABASE_URL = f"sqlite+aiosqlite:///{SQLITE_DB_PATH}"
    SYNC_DATABASE_URL = f"sqlite:///{SQLITE_DB_PATH}"
else:
    # PostgreSQL configuration
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "user")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "credit_risk_db")
    
    DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    SYNC_DATABASE_URL = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"


def generate_uuid():
    return str(uuid.uuid4())


class ApplicationDB(Base):
    __tablename__ = "applications"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    
    # Applicant Info
    applicant_name = Column(String(100), nullable=False)
    applicant_email = Column(String(255), nullable=False)
    applicant_phone = Column(String(20))
    applicant_age = Column(Integer)
    ssn_last_four = Column(String(4))
    
    # Loan Details
    loan_amount = Column(Float, nullable=False)
    loan_purpose = Column(String(50))
    loan_term_months = Column(Integer)
    collateral_type = Column(String(50))
    collateral_value = Column(Float)
    
    # Employment Info
    employment_status = Column(String(50))
    employer_name = Column(String(100))
    job_title = Column(String(100))
    years_employed = Column(Float)
    annual_income = Column(Float)
    
    # Credit Info
    credit_score = Column(Integer)
    years_credit_history = Column(Float)
    num_credit_lines = Column(Integer)
    credit_utilization = Column(Float)
    delinquencies_2yrs = Column(Integer, default=0)
    public_records = Column(Integer, default=0)
    hard_inquiries_6mo = Column(Integer, default=0)
    
    # Financial Info
    monthly_debt = Column(Float)
    savings = Column(Float, default=0)
    checking_balance = Column(Float, default=0)
    investment_accounts = Column(Float, default=0)
    other_income = Column(Float, default=0)
    
    # Status
    status = Column(String(20), default="pending")
    current_agent = Column(String(50))
    
    # Timestamps
    submitted_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    
    # Relationships
    documents = relationship("DocumentDB", back_populates="application")
    decision = relationship("DecisionDB", back_populates="application", uselist=False)


class DocumentDB(Base):
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    application_id = Column(String(36), ForeignKey("applications.id"))
    
    filename = Column(String(255))
    document_type = Column(String(50))
    s3_key = Column(String(500))
    
    verified = Column(Boolean, default=False)
    verification_status = Column(String(50))
    extracted_data = Column(JSON)
    fraud_risk_score = Column(Float, default=0)
    
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    verified_at = Column(DateTime)
    
    application = relationship("ApplicationDB", back_populates="documents")


class DecisionDB(Base):
    __tablename__ = "decisions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    application_id = Column(String(36), ForeignKey("applications.id"), unique=True)
    
    # Decision
    decision = Column(String(20))  # APPROVE, DENY, CONDITIONAL
    confidence = Column(Float)
    
    # Risk Assessment
    default_probability = Column(Float)
    risk_level = Column(String(20))
    risk_score = Column(Float)
    risk_factors = Column(JSON)
    
    # Agent Results
    agent_results = Column(JSON)
    
    # Approved Terms
    approved_amount = Column(Float)
    interest_rate = Column(Float)
    approved_term_months = Column(Integer)
    monthly_payment = Column(Float)
    conditions = Column(JSON)
    
    # Explanations
    decision_reasoning = Column(Text)
    customer_explanation = Column(Text)
    adverse_action_notice = Column(Text)
    improvement_suggestions = Column(JSON)
    next_steps = Column(Text)
    
    # Metadata
    processing_time_ms = Column(Integer)
    decided_at = Column(DateTime, default=datetime.utcnow)
    decided_by = Column(String(100), default="AI Underwriting System")
    
    application = relationship("ApplicationDB", back_populates="decision")


class AgentLogDB(Base):
    __tablename__ = "agent_logs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    application_id = Column(String(36), ForeignKey("applications.id"))
    
    agent_name = Column(String(50))
    status = Column(String(20))
    processing_time_ms = Column(Integer)
    confidence = Column(Float)
    
    input_data = Column(JSON)
    output_data = Column(JSON)
    reasoning = Column(Text)
    error_message = Column(Text)
    
    started_at = Column(DateTime)
    completed_at = Column(DateTime, default=datetime.utcnow)


# Engine and Session
async_engine = create_async_engine(DATABASE_URL, echo=False)
sync_engine = create_engine(SYNC_DATABASE_URL, echo=False)

AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=sync_engine)
    print("Database tables created successfully")


if __name__ == "__main__":
    init_db()
