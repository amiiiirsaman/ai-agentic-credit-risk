/**
 * TypeScript type definitions for the Credit Risk Assessment Platform
 */

// Enums as const objects for runtime use
export enum LoanType {
  PERSONAL = 'personal',
  HOME_PURCHASE = 'home_purchase',
  REFINANCE = 'refinance',
  AUTO = 'auto',
  BUSINESS = 'business',
  STUDENT = 'education',
  DEBT_CONSOLIDATION = 'debt_consolidation',
}

export enum RiskProfile {
  LOW = 'low_risk',
  MEDIUM = 'medium_risk',
  HIGH = 'high_risk',
}

export enum EmploymentStatus {
  EMPLOYED = 'employed',
  SELF_EMPLOYED = 'self_employed',
  UNEMPLOYED = 'unemployed',
  RETIRED = 'retired',
  STUDENT = 'student',
}

export enum AgentStatus {
  PENDING = 'PENDING',
  PROCESSING = 'PROCESSING',
  COMPLETED = 'COMPLETED',
  ERROR = 'ERROR',
}

export enum DecisionType {
  APPROVED = 'APPROVED',
  DENIED = 'DENIED',
  CONDITIONAL = 'CONDITIONAL',
  PENDING = 'PENDING',
}

// Type aliases
export type LoanPurpose = 
  | 'home_purchase' 
  | 'refinance' 
  | 'debt_consolidation' 
  | 'business' 
  | 'personal' 
  | 'auto' 
  | 'education' 
  | 'other';

export type HomeOwnership = 'own' | 'mortgage' | 'rent' | 'other';

export type ApplicationStatus = 
  | 'pending' 
  | 'processing' 
  | 'approved' 
  | 'denied' 
  | 'conditional';

export type RiskLevel = 'Low' | 'Medium' | 'High' | 'Critical';

// Application Models
export interface ApplicantInfo {
  name: string;
  email: string;
  phone: string;
  age: number;
  ssn_last_four?: string;
}

export interface LoanDetails {
  amount: number;
  purpose: LoanPurpose;
  term_months: number;
  collateral_type?: string;
  collateral_value?: number;
}

export interface EmploymentInfo {
  status: EmploymentStatus;
  employer_name?: string;
  job_title?: string;
  years_employed: number;
  annual_income: number;
  monthly_income?: number;
}

export interface CreditInfo {
  credit_score: number;
  years_credit_history: number;
  num_credit_lines: number;
  credit_utilization: number;
  delinquencies_2yrs: number;
  public_records: number;
  hard_inquiries_6mo: number;
}

export interface FinancialInfo {
  monthly_debt: number;
  savings: number;
  checking_balance: number;
  investment_accounts: number;
  other_income: number;
}

export interface DocumentInfo {
  id: string;
  filename: string;
  document_type: string;
  uploaded_at: string;
  verified: boolean;
  verification_status?: string;
}

export interface LoanApplication {
  applicant: ApplicantInfo;
  loan: LoanDetails;
  employment: EmploymentInfo;
  credit: CreditInfo;
  financial: FinancialInfo;
  documents: DocumentInfo[];
}

// Response Models
export interface RiskFactor {
  feature: string;
  impact: number;
  direction: 'positive' | 'negative';
  description: string;
}

export interface AgentResult {
  agent_name: string;
  status: 'completed' | 'failed' | 'skipped';
  processing_time_ms: number;
  confidence: number;
  output: Record<string, unknown>;
  reasoning?: string;
}

export interface LoanTerms {
  approved_amount: number;
  interest_rate: number;
  term_months: number;
  monthly_payment: number;
  total_interest: number;
  conditions: string[];
}

export interface UnderwritingDecision {
  application_id: string;
  decision: DecisionType;
  confidence: number;
  default_probability: number;
  risk_level: RiskLevel;
  risk_factors: RiskFactor[];
  agent_results: Record<string, AgentResult>;
  loan_terms?: LoanTerms;
  decision_reasoning: string;
  customer_explanation: string;
  adverse_action_notice?: string;
  improvement_suggestions: string[];
  next_steps: string;
  processing_time_ms: number;
  decided_at: string;
  decided_by: string;
}

export interface ApplicationResponse {
  application_id: string;
  status: ApplicationStatus;
  submitted_at: string;
  message: string;
}

export interface ApplicationStatusResponse {
  application_id: string;
  status: ApplicationStatus;
  current_agent?: string;
  agents_completed: string[];
  progress_percent: number;
  estimated_completion_seconds?: number;
}

export interface DashboardMetrics {
  total_applications: number;
  approved_count: number;
  denied_count: number;
  conditional_count: number;
  pending_count: number;
  approval_rate: number;
  avg_processing_time_ms: number;
  avg_default_probability: number;
  total_loan_volume: number;
}

// Agent Status
export interface AgentHealth {
  agent_name: string;
  status: 'healthy' | 'degraded' | 'unhealthy';
  last_check: string;
  avg_response_time_ms: number;
  success_rate: number;
}

export interface SystemHealth {
  status: string;
  agents: AgentHealth[];
  database_connected: boolean;
  aws_bedrock_connected: boolean;
  uptime_seconds: number;
}

// UI State
export interface FormStep {
  id: number;
  title: string;
  description: string;
  completed: boolean;
}

export interface ProcessingStep {
  name: string;
  agent: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  time_ms?: number;
}
