import axios from 'axios';
import type { 
  LoanApplication, 
  ApplicationResponse, 
  ApplicationStatusResponse,
  UnderwritingDecision,
  DashboardMetrics 
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Application APIs
export const submitApplication = async (application: LoanApplication): Promise<ApplicationResponse> => {
  const response = await api.post('/applications', application);
  return response.data;
};

export const getApplication = async (applicationId: string) => {
  const response = await api.get(`/applications/${applicationId}`);
  return response.data;
};

export const getApplicationStatus = async (applicationId: string): Promise<ApplicationStatusResponse> => {
  const response = await api.get(`/applications/${applicationId}/status`);
  return response.data;
};

export const listApplications = async (params?: { status?: string; limit?: number; offset?: number }) => {
  const response = await api.get('/applications', { params });
  return response.data;
};

// Decision APIs
export const getDecision = async (applicationId: string): Promise<UnderwritingDecision> => {
  const response = await api.get(`/decisions/${applicationId}`);
  return response.data;
};

export const getDecisionExplanation = async (applicationId: string) => {
  const response = await api.get(`/decisions/${applicationId}/explanation`);
  return response.data;
};

// Underwriting APIs
export const triggerUnderwriting = async (applicationId: string) => {
  const response = await api.post(`/underwrite/${applicationId}`);
  return response.data;
};

export const underwriteSync = async (application: LoanApplication) => {
  const response = await api.post('/underwrite/sync', application);
  return response.data;
};

// Synthetic Data APIs
export const getSyntheticApplication = async (riskProfile: string = 'random') => {
  const response = await api.get('/synthetic/application', { params: { risk_profile: riskProfile } });
  return response.data;
};

export const generateBatchApplications = async (count: number = 10) => {
  const response = await api.post('/synthetic/batch', null, { params: { count } });
  return response.data;
};

// Analytics APIs
export const getDashboardMetrics = async (): Promise<DashboardMetrics> => {
  const response = await api.get('/analytics/dashboard');
  return response.data;
};

export const getAgentPerformance = async () => {
  const response = await api.get('/analytics/agent-performance');
  return response.data;
};

// System APIs
export const getAgentsStatus = async () => {
  const response = await api.get('/agents/status');
  return response.data;
};

export const healthCheck = async () => {
  const response = await axios.get('/health');
  return response.data;
};

export default api;
