/**
 * Formatting utilities for the Credit Risk Assessment Platform
 */

export const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
};

export const formatCurrencyWithCents = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
};

export const formatPercent = (value: number, decimals: number = 1): string => {
  return `${(value * 100).toFixed(decimals)}%`;
};

export const formatPercentRaw = (value: number, decimals: number = 1): string => {
  return `${value.toFixed(decimals)}%`;
};

export const formatNumber = (value: number): string => {
  return new Intl.NumberFormat('en-US').format(value);
};

export const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
};

export const formatDateTime = (dateString: string): string => {
  return new Date(dateString).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

export const formatDuration = (ms: number): string => {
  if (ms < 1000) {
    return `${ms}ms`;
  }
  const seconds = ms / 1000;
  if (seconds < 60) {
    return `${seconds.toFixed(1)}s`;
  }
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.floor(seconds % 60);
  return `${minutes}m ${remainingSeconds}s`;
};

export const formatPhoneNumber = (phone: string): string => {
  const cleaned = phone.replace(/\D/g, '');
  if (cleaned.length === 10) {
    return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
  }
  if (cleaned.length === 11 && cleaned.startsWith('1')) {
    return `+1 (${cleaned.slice(1, 4)}) ${cleaned.slice(4, 7)}-${cleaned.slice(7)}`;
  }
  return phone;
};

export const formatCreditScore = (score: number): string => {
  if (score >= 750) return `${score} (Excellent)`;
  if (score >= 700) return `${score} (Good)`;
  if (score >= 650) return `${score} (Fair)`;
  if (score >= 580) return `${score} (Poor)`;
  return `${score} (Very Poor)`;
};

export const getRiskLevelColor = (level: string): string => {
  const colors: Record<string, string> = {
    Low: 'text-success-600',
    Medium: 'text-warning-600',
    High: 'text-danger-500',
    Critical: 'text-danger-700',
  };
  return colors[level] || 'text-gray-600';
};

export const getRiskLevelBgColor = (level: string): string => {
  const colors: Record<string, string> = {
    Low: 'bg-success-100',
    Medium: 'bg-warning-100',
    High: 'bg-danger-100',
    Critical: 'bg-danger-200',
  };
  return colors[level] || 'bg-gray-100';
};

export const getDecisionColor = (decision: string): { bg: string; text: string } => {
  const colors: Record<string, { bg: string; text: string }> = {
    APPROVED: { bg: 'bg-green-100', text: 'text-green-600' },
    APPROVE: { bg: 'bg-green-100', text: 'text-green-600' },
    CONDITIONAL: { bg: 'bg-yellow-100', text: 'text-yellow-600' },
    DENIED: { bg: 'bg-red-100', text: 'text-red-600' },
    DENY: { bg: 'bg-red-100', text: 'text-red-600' },
    PENDING: { bg: 'bg-gray-100', text: 'text-gray-600' },
  };
  return colors[decision] || { bg: 'bg-gray-100', text: 'text-gray-600' };
};

export const getRiskColor = (level: string): { bg: string; text: string } => {
  const colors: Record<string, { bg: string; text: string }> = {
    LOW: { bg: 'bg-green-100', text: 'text-green-600' },
    Low: { bg: 'bg-green-100', text: 'text-green-600' },
    MEDIUM: { bg: 'bg-yellow-100', text: 'text-yellow-600' },
    Medium: { bg: 'bg-yellow-100', text: 'text-yellow-600' },
    HIGH: { bg: 'bg-red-100', text: 'text-red-600' },
    High: { bg: 'bg-red-100', text: 'text-red-600' },
    CRITICAL: { bg: 'bg-red-200', text: 'text-red-700' },
    Critical: { bg: 'bg-red-200', text: 'text-red-700' },
  };
  return colors[level] || { bg: 'bg-gray-100', text: 'text-gray-600' };
};

export const getDecisionBgColor = (decision: string): string => {
  const colors: Record<string, string> = {
    APPROVE: 'bg-success-100',
    CONDITIONAL: 'bg-warning-100',
    DENY: 'bg-danger-100',
  };
  return colors[decision] || 'bg-gray-100';
};

export const getStatusColor = (status: string): string => {
  const colors: Record<string, string> = {
    pending: 'text-gray-600',
    processing: 'text-primary-600',
    approved: 'text-success-600',
    denied: 'text-danger-600',
    conditional: 'text-warning-600',
    completed: 'text-success-600',
    failed: 'text-danger-600',
  };
  return colors[status] || 'text-gray-600';
};

export const getStatusBgColor = (status: string): string => {
  const colors: Record<string, string> = {
    pending: 'bg-gray-100',
    processing: 'bg-primary-100',
    approved: 'bg-success-100',
    denied: 'bg-danger-100',
    conditional: 'bg-warning-100',
    completed: 'bg-success-100',
    failed: 'bg-danger-100',
  };
  return colors[status] || 'bg-gray-100';
};

export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text;
  return `${text.slice(0, maxLength)}...`;
};

export const capitalizeFirst = (text: string): string => {
  return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
};

export const formatLoanPurpose = (purpose: string): string => {
  const purposes: Record<string, string> = {
    home_purchase: 'Home Purchase',
    refinance: 'Refinance',
    debt_consolidation: 'Debt Consolidation',
    business: 'Business',
    personal: 'Personal',
    auto: 'Auto',
    education: 'Education',
    other: 'Other',
  };
  return purposes[purpose] || capitalizeFirst(purpose.replace(/_/g, ' '));
};

export const formatEmploymentStatus = (status: string): string => {
  const statuses: Record<string, string> = {
    employed: 'Employed',
    self_employed: 'Self-Employed',
    retired: 'Retired',
    unemployed: 'Unemployed',
    student: 'Student',
  };
  return statuses[status] || capitalizeFirst(status.replace(/_/g, ' '));
};
