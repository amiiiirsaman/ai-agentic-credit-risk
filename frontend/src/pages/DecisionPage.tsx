import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceDot,
} from 'recharts';
import {
  DocumentTextIcon,
  ShieldCheckIcon,
  CurrencyDollarIcon,
  ChartBarIcon,
  CalculatorIcon,
  HomeIcon,
  UserGroupIcon,
  ArrowTrendingUpIcon,
  ScaleIcon,
  UserIcon,
  LightBulbIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  CpuChipIcon,
  BriefcaseIcon,
  BanknotesIcon,
  IdentificationIcon,
} from '@heroicons/react/24/outline';
import { formatCurrency, formatPercent } from '../utils/format';

// Agent display configuration with Heroicons
const AGENT_CONFIG: Record<string, { name: string; Icon: React.ComponentType<any>; color: string; description: string }> = {
  document_intelligence: {
    name: 'Document Intelligence',
    Icon: DocumentTextIcon,
    color: '#3b82f6',
    description: 'Analyzes and verifies submitted documents for authenticity and completeness'
  },
  fraud_detection: {
    name: 'Fraud Detection',
    Icon: ShieldCheckIcon,
    color: '#ef4444',
    description: 'Detects synthetic identity fraud, anomalies, and suspicious patterns'
  },
  income_verification: {
    name: 'Income Verification',
    Icon: CurrencyDollarIcon,
    color: '#10b981',
    description: 'Validates income sources, employment stability, and DTI ratio'
  },
  credit_history: {
    name: 'Credit History',
    Icon: ChartBarIcon,
    color: '#8b5cf6',
    description: 'Analyzes credit report, payment behavior, and credit trajectory'
  },
  quantitative_risk: {
    name: 'Quantitative Risk',
    Icon: CalculatorIcon,
    color: '#f59e0b',
    description: 'ML-based default probability calculation with SHAP explanations'
  },
  collateral: {
    name: 'Collateral',
    Icon: HomeIcon,
    color: '#06b6d4',
    description: 'Evaluates collateral value, LTV ratio, and security coverage'
  },
  customer_relationship: {
    name: 'Customer Relations',
    Icon: UserGroupIcon,
    color: '#ec4899',
    description: 'Assesses customer history, relationship depth, and loyalty indicators'
  },
  market_conditions: {
    name: 'Market Conditions',
    Icon: ArrowTrendingUpIcon,
    color: '#84cc16',
    description: 'Evaluates economic factors, industry trends, and market risks'
  },
  compliance: {
    name: 'Compliance',
    Icon: ScaleIcon,
    color: '#6366f1',
    description: 'Ensures FCRA, ECOA, and fair lending compliance'
  },
  chief_underwriter: {
    name: 'Chief Underwriter',
    Icon: UserIcon,
    color: '#1e3a5f',
    description: 'Final decision authority aggregating all agent assessments'
  },
  explainability: {
    name: 'Explainability',
    Icon: LightBulbIcon,
    color: '#f97316',
    description: 'Generates customer-friendly explanations and improvement suggestions'
  },
};

const AGENT_ORDER = [
  'document_intelligence', 'fraud_detection', 'income_verification', 'credit_history',
  'quantitative_risk', 'collateral', 'customer_relationship', 'market_conditions',
  'compliance', 'chief_underwriter', 'explainability'
];

// Generate synthetic risk distribution data for visualization
const generateRiskDistribution = (riskLevel: string, defaultProb: number | null) => {
  const distributions: Record<string, number[]> = {
    'Low': [8, 15, 28, 42, 55, 62, 58, 45, 32, 20, 12, 6, 3],
    'Medium': [3, 8, 16, 28, 42, 55, 62, 55, 42, 28, 16, 8, 3],
    'High': [2, 5, 10, 18, 28, 38, 48, 55, 58, 52, 38, 25, 15],
    'Critical': [1, 3, 6, 12, 18, 25, 32, 42, 52, 58, 62, 55, 40],
  };
  
  const dist = distributions[riskLevel] || distributions['Medium'];
  const data = dist.map((value, index) => ({
    x: index * 8 + 4,
    count: value + Math.floor(Math.random() * 5),
  }));
  
  // Only calculate applicant position if defaultProb is valid
  if (defaultProb === null || isNaN(defaultProb)) {
    return { data, applicantX: null, applicantY: null };
  }
  
  // Find Y value (count) at applicant's X position for the dot
  const applicantX = Math.min(Math.max(Math.round(defaultProb * 100), 4), 100);
  const nearestIndex = Math.min(Math.floor(applicantX / 8), dist.length - 1);
  const applicantY = data[nearestIndex]?.count || 35;
  
  return { data, applicantX, applicantY };
};

interface AgentResult {
  agent: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  result?: any;
}

interface LogEntry {
  timestamp: string;
  type: 'info' | 'agent_start' | 'agent_complete' | 'nova_call' | 'error' | 'success';
  message: string;
}

export default function DecisionPage() {
  const { applicationId } = useParams<{ applicationId: string }>();
  const [decision, setDecision] = useState<any>(null);
  const [processing, setProcessing] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [agents, setAgents] = useState<AgentResult[]>(
    AGENT_ORDER.map(agent => ({ agent, status: 'pending' }))
  );
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [expandedAgent, setExpandedAgent] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const logsRef = useRef<HTMLDivElement>(null);
  const startTimeRef = useRef(Date.now());

  const addLog = useCallback((type: LogEntry['type'], message: string) => {
    setLogs(prev => [...prev, {
      timestamp: new Date().toLocaleTimeString('en-US', { hour12: false }),
      type,
      message
    }]);
  }, []);

  // WebSocket connection for real-time updates
  useEffect(() => {
    if (!applicationId) return;

    const wsUrl = `ws://localhost:8000/ws/${applicationId}`;
    addLog('info', `Connecting to ${wsUrl}...`);
    
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => addLog('success', 'Connected! Waiting for agent updates...');

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'agent_update') {
          const agentKey = data.agent;
          const config = AGENT_CONFIG[agentKey];
          
          if (data.status === 'processing') {
            addLog('agent_start', `[${config?.name || agentKey}] Starting analysis...`);
            addLog('nova_call', `   → Invoking AWS Bedrock Nova Pro...`);
            setAgents(prev => prev.map(a => 
              a.agent === agentKey ? { ...a, status: 'processing' } : a
            ));
          } else if (data.status === 'completed') {
            const confidence = data.result?.confidence || data.result?.output?.confidence || 0.85;
            addLog('agent_complete', `[${config?.name || agentKey}] Completed (${(confidence * 100).toFixed(0)}%)`);
            setAgents(prev => prev.map(a => 
              a.agent === agentKey ? { ...a, status: 'completed', result: data.result } : a
            ));
          }
        } else if (data.type === 'processing_started') {
          addLog('info', 'Processing started - 11 agents will analyze sequentially');
        } else if (data.type === 'processing_completed') {
          addLog('success', 'All agents completed! Decision ready.');
          setDecision(data.decision);
          setProcessing(false);
          setAgents(prev => prev.map(a => ({ ...a, status: 'completed' })));
        } else if (data.type === 'processing_failed') {
          addLog('error', `Processing failed: ${data.error}`);
          setError(data.error);
          setProcessing(false);
        }
      } catch (e) {
        console.error('WebSocket parse error:', e);
      }
    };

    ws.onerror = () => addLog('error', 'WebSocket connection error');
    ws.onclose = () => addLog('info', 'Connection closed');

    return () => { if (ws.readyState === WebSocket.OPEN) ws.close(); };
  }, [applicationId, addLog]);

  // Timer for elapsed time
  useEffect(() => {
    if (!processing) return;
    const interval = setInterval(() => setElapsedTime(Date.now() - startTimeRef.current), 100);
    return () => clearInterval(interval);
  }, [processing]);

  // Auto-scroll logs
  useEffect(() => {
    if (logsRef.current) logsRef.current.scrollTop = logsRef.current.scrollHeight;
  }, [logs]);

  // Calculate progress
  const completedCount = agents.filter(a => a.status === 'completed').length;
  const progress = (completedCount / agents.length) * 100;

  // Extract decision data - use null coalescing only for truly missing data
  const decisionData = decision?.decision || {};
  const applicationData = decision?.application_data || {};
  const decisionType = decisionData.decision || 'PENDING';
  // Only use fallback if value is truly undefined/null, not if it's 0
  const confidenceScore = decisionData.confidence_score ?? decisionData.confidence ?? null;
  const riskLevel = decisionData.risk_level || 'Unknown';
  const defaultProb = decisionData.default_probability ?? null;
  const riskPercentile = decisionData.risk_percentile ?? null;
  
  // Check if we have valid metrics to display
  const hasValidMetrics = confidenceScore !== null && defaultProb !== null;

  // Prepare radar chart data from agents state (which has live results)
  const radarData = agents
    .filter(a => a.status === 'completed' && a.result && !['chief_underwriter', 'explainability'].includes(a.agent))
    .map(a => {
      // Use actual confidence - no fallback to fixed value
      const conf = a.result?.confidence ?? a.result?.output?.confidence ?? 0.5; // 0.5 = uncertain, not 0.8
      return {
        agent: AGENT_CONFIG[a.agent]?.name.split(' ')[0].slice(0, 8) || a.agent.slice(0, 8),
        confidence: conf * 100,
      };
    });

  // Generate risk distribution data with applicant position
  const { data: distributionData, applicantX, applicantY } = generateRiskDistribution(riskLevel, defaultProb);

  // Style helpers
  const getDecisionStyle = () => {
    switch (decisionType) {
      case 'APPROVE': return { bg: 'from-emerald-500 to-green-600', text: 'text-white', icon: '✓', glow: 'shadow-green-500/50' };
      case 'DENY': return { bg: 'from-red-500 to-rose-600', text: 'text-white', icon: '✗', glow: 'shadow-red-500/50' };
      case 'CONDITIONAL': return { bg: 'from-amber-500 to-orange-600', text: 'text-white', icon: '!', glow: 'shadow-amber-500/50' };
      default: return { bg: 'from-slate-500 to-slate-600', text: 'text-white', icon: '?', glow: 'shadow-slate-500/50' };
    }
  };

  const getRiskColor = () => {
    switch (riskLevel) {
      case 'Low': return { color: 'text-emerald-400', bg: 'bg-emerald-500', chartColor: '#10b981' };
      case 'Medium': return { color: 'text-amber-400', bg: 'bg-amber-500', chartColor: '#f59e0b' };
      case 'High': return { color: 'text-orange-400', bg: 'bg-orange-500', chartColor: '#f97316' };
      case 'Critical': return { color: 'text-red-400', bg: 'bg-red-500', chartColor: '#ef4444' };
      default: return { color: 'text-slate-400', bg: 'bg-slate-500', chartColor: '#64748b' };
    }
  };

  const decisionStyle = getDecisionStyle();
  const riskStyle = getRiskColor();

  // Toggle agent expansion
  const toggleAgent = (agentKey: string) => {
    const agent = agents.find(a => a.agent === agentKey);
    if (agent?.status === 'completed' && agent.result) {
      setExpandedAgent(expandedAgent === agentKey ? null : agentKey);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">AI Credit Risk Assessment</h1>
          <p className="text-slate-400">
            Application: <span className="font-mono text-blue-400">{applicationId}</span>
          </p>
          
          {/* Status Badge */}
          <div className="mt-4 inline-flex items-center gap-4 px-6 py-3 bg-slate-800/50 backdrop-blur border border-slate-700 rounded-full">
            <div className="flex items-center">
              {processing ? (
                <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse mr-2" />
              ) : (
                <div className="w-3 h-3 bg-green-500 rounded-full mr-2" />
              )}
              <span className="font-mono text-white">{(elapsedTime / 1000).toFixed(1)}s</span>
            </div>
            <div className="w-px h-6 bg-slate-600" />
            <span className="text-green-400 font-medium">{completedCount}/{agents.length} agents</span>
            <div className="w-px h-6 bg-slate-600" />
            <span className={processing ? 'text-amber-400' : 'text-green-400'}>
              {processing ? 'Processing...' : 'Complete'}
            </span>
          </div>
        </motion.div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-blue-500 via-purple-500 to-green-500"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
        </div>

        {/* Main Grid - Agent Pipeline & Logs */}
        <div className="grid lg:grid-cols-2 gap-6 mb-8">
          {/* Agent Status Panel with Expandable Cards */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-slate-800/50 backdrop-blur rounded-2xl border border-slate-700 p-6"
          >
            <h2 className="text-xl font-bold text-white mb-4 flex items-center">
              <CpuChipIcon className="w-6 h-6 mr-2 text-blue-400" /> Agent Pipeline
              <span className="ml-auto text-sm font-normal text-slate-400">Click completed agents for details</span>
            </h2>
            
            <div className="space-y-2 max-h-[600px] overflow-y-auto pr-2">
              {agents.map((agent, idx) => {
                const config = AGENT_CONFIG[agent.agent];
                const isExpanded = expandedAgent === agent.agent;
                const hasResult = agent.status === 'completed' && agent.result;
                
                return (
                  <div key={agent.agent}>
                    {/* Agent Card Header */}
                    <motion.div
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.03 }}
                      onClick={() => toggleAgent(agent.agent)}
                      className={`flex items-center justify-between p-3 rounded-xl border transition-all cursor-pointer ${
                        agent.status === 'completed'
                          ? 'bg-slate-700/50 border-green-500/50 hover:border-green-400 hover:bg-slate-700'
                          : agent.status === 'processing'
                          ? 'bg-blue-900/30 border-blue-500 shadow-lg shadow-blue-500/20'
                          : 'bg-slate-800/50 border-slate-600'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        {config?.Icon && (
                          <config.Icon 
                            className={`w-6 h-6 ${
                              agent.status === 'completed' ? 'text-green-400' :
                              agent.status === 'processing' ? 'text-blue-400' : 'text-slate-500'
                            }`}
                          />
                        )}
                        <div>
                          <span className={`font-medium ${
                            agent.status === 'completed' ? 'text-green-400' :
                            agent.status === 'processing' ? 'text-blue-400' : 'text-slate-400'
                          }`}>
                            {config?.name || agent.agent}
                          </span>
                          {agent.status === 'processing' && (
                            <p className="text-xs text-blue-300 animate-pulse">Calling Nova Pro...</p>
                          )}
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        {agent.status === 'completed' && (
                          <span className="text-sm font-bold text-green-400 bg-green-500/20 px-2 py-0.5 rounded">
                            {formatPercent(agent.result?.confidence ?? agent.result?.output?.confidence ?? 0.5)}
                          </span>
                        )}
                        {agent.status === 'processing' && (
                          <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                        )}
                        {agent.status === 'pending' && (
                          <div className="w-5 h-5 border-2 border-slate-500 rounded-full" />
                        )}
                        {hasResult && (
                          <motion.span 
                            animate={{ rotate: isExpanded ? 180 : 0 }}
                            className="text-slate-400 ml-1"
                          >
                            ▼
                          </motion.span>
                        )}
                      </div>
                    </motion.div>
                    
                    {/* Expandable Agent Details */}
                    <AnimatePresence>
                      {isExpanded && hasResult && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.2 }}
                          className="overflow-hidden"
                        >
                          <div className="mt-2 p-4 bg-slate-900/80 rounded-xl border border-slate-600 ml-4">
                            {/* Agent Description */}
                            <p className="text-xs text-slate-500 mb-3 italic">{config?.description}</p>
                            
                            {/* Decision Badge for this agent */}
                            {agent.result?.output?.decision && (
                              <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-bold mb-3 ${
                                agent.result.output.decision === 'APPROVE' || agent.result.output.approved ? 'bg-green-500/20 text-green-400' :
                                agent.result.output.decision === 'DENY' || agent.result.output.rejected ? 'bg-red-500/20 text-red-400' :
                                'bg-amber-500/20 text-amber-400'
                              }`}>
                                {agent.result.output.decision || (agent.result.output.approved ? 'PASS' : 'FLAG')}
                              </div>
                            )}
                            
                            {/* Key Findings Grid */}
                            <div className="grid grid-cols-2 gap-2 text-sm">
                              {agent.result?.output && Object.entries(agent.result.output)
                                .filter(([key, value]) => {
                                  // Exclude known long-text fields and reasoning
                                  const excludeKeys = ['reasoning', 'recommendation', 'summary', 'raw_response', 
                                    'relationship_notes', 'notes', 'comments', 'explanation', 'description',
                                    'customer_explanation', 'adverse_action_notice', 'next_steps'];
                                  if (excludeKeys.includes(key)) return false;
                                  // Exclude string values longer than 60 chars (they won't display well)
                                  if (typeof value === 'string' && value.length > 60) return false;
                                  // Exclude nested objects (except arrays)
                                  if (typeof value === 'object' && value !== null && !Array.isArray(value)) return false;
                                  return true;
                                })
                                .slice(0, 8)
                                .map(([key, value]) => (
                                <div key={key} className="flex justify-between bg-slate-800/50 rounded px-2 py-1">
                                  <span className="text-slate-400 text-xs capitalize">
                                    {key.replace(/_/g, ' ')}:
                                  </span>
                                  <span className="text-white font-medium text-xs">
                                    {typeof value === 'number' 
                                      ? (value < 1 && value > 0 ? formatPercent(value) : value.toFixed(2))
                                      : typeof value === 'boolean' 
                                      ? (value ? '✓' : '✗')
                                      : typeof value === 'string' 
                                      ? value
                                      : Array.isArray(value)
                                      ? `${value.length} items`
                                      : '-'}
                                  </span>
                                </div>
                              ))}
                            </div>
                            
                            {/* Nova Pro Reasoning */}
                            {(agent.result?.output?.reasoning || agent.result?.output?.recommendation) && (
                              <div className="mt-3 pt-3 border-t border-slate-700">
                                <p className="text-xs text-purple-400 font-semibold mb-1">🤖 Nova Pro Analysis:</p>
                                <p className="text-slate-300 text-xs leading-relaxed">
                                  {(agent.result.output.reasoning || agent.result.output.recommendation || '').slice(0, 300)}
                                  {(agent.result.output.reasoning || agent.result.output.recommendation || '').length > 300 && '...'}
                                </p>
                              </div>
                            )}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                );
              })}
            </div>
          </motion.div>

          {/* Live Log Panel */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-slate-800/50 backdrop-blur rounded-2xl border border-slate-700 p-6"
          >
            <h2 className="text-xl font-bold text-white mb-4 flex items-center">
              <DocumentTextIcon className="w-6 h-6 mr-2 text-green-400" /> Processing Log
            </h2>
            
            <div ref={logsRef} className="bg-black/60 rounded-xl p-4 h-[600px] overflow-y-auto font-mono text-xs">
              {logs.map((log, i) => (
                <div key={i} className="mb-1">
                  <span className="text-slate-500">[{log.timestamp}]</span>
                  <span className={
                    log.type === 'success' ? ' text-green-400 font-bold' :
                    log.type === 'error' ? ' text-red-400' :
                    log.type === 'agent_start' ? ' text-yellow-400' :
                    log.type === 'agent_complete' ? ' text-green-400' :
                    log.type === 'nova_call' ? ' text-purple-400' :
                    ' text-slate-300'
                  }> {log.message}</span>
                </div>
              ))}
              <span className="text-green-500 animate-pulse">▌</span>
            </div>
          </motion.div>
        </div>

        {/* AWS Bedrock Badge */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="mb-8 bg-gradient-to-r from-purple-900/30 to-blue-900/30 rounded-xl p-3 border border-purple-500/30"
        >
          <div className="flex items-center justify-center text-sm gap-3">
            <CpuChipIcon className="w-5 h-5 text-purple-400" />
            <span className="text-purple-400">Powered by</span>
            <span className="text-white font-bold">AWS Bedrock</span>
            <span className="text-slate-500">|</span>
            <span className="text-blue-400">amazon.nova-pro-v1:0</span>
          </div>
        </motion.div>

        {/* ============ DECISION RESULTS (shown inline when processing complete) ============ */}
        <AnimatePresence>
          {!processing && decision && (
            <motion.div
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, ease: 'easeOut' }}
            >
              {/* Decision Hero Card */}
              <div className={`relative overflow-hidden bg-gradient-to-r ${decisionStyle.bg} rounded-3xl p-8 mb-8 shadow-2xl ${decisionStyle.glow}`}>
                {/* Background Pattern */}
                <div className="absolute inset-0 opacity-10">
                  <div className="absolute inset-0" style={{ backgroundImage: 'radial-gradient(circle at 2px 2px, white 1px, transparent 0)', backgroundSize: '32px 32px' }} />
                </div>
                
                <div className="relative flex flex-col lg:flex-row items-center justify-between gap-8">
                  {/* Decision Badge */}
                  <div className="text-center lg:text-left">
                    <motion.div 
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ type: 'spring', stiffness: 200, delay: 0.2 }}
                      className="inline-flex items-center justify-center w-28 h-28 bg-white/20 backdrop-blur rounded-full mb-4 shadow-lg"
                    >
                      {decisionType === 'APPROVE' ? (
                        <CheckCircleIcon className="w-16 h-16 text-white" />
                      ) : decisionType === 'DENY' ? (
                        <XCircleIcon className="w-16 h-16 text-white" />
                      ) : (
                        <ExclamationTriangleIcon className="w-16 h-16 text-white" />
                      )}
                    </motion.div>
                    <h2 className="text-5xl font-black text-white mb-2 tracking-tight">{decisionType}</h2>
                    <p className="text-white/80 max-w-md">
                      {decisionData.decision_reasoning?.slice(0, 120) || 'Decision rendered based on comprehensive agent analysis'}...
                    </p>
                  </div>
                  
                  {/* Key Metrics Grid - Only show metrics that have values */}
                  <div className={`grid gap-4 ${
                    [confidenceScore !== null, riskLevel && riskLevel !== 'Unknown', defaultProb !== null, true].filter(Boolean).length === 4 
                      ? 'grid-cols-2 lg:grid-cols-4' 
                      : [confidenceScore !== null, riskLevel && riskLevel !== 'Unknown', defaultProb !== null, true].filter(Boolean).length === 3
                      ? 'grid-cols-3'
                      : 'grid-cols-2'
                  }`}>
                    {confidenceScore !== null && (
                      <motion.div 
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3 }}
                        className="bg-white/10 backdrop-blur rounded-2xl p-4 text-center min-w-[120px]"
                      >
                        <p className="text-white/60 text-sm mb-1">Confidence</p>
                        <p className="text-4xl font-black text-white">{formatPercent(confidenceScore)}</p>
                      </motion.div>
                    )}
                    {riskLevel && riskLevel !== 'Unknown' && (
                      <motion.div 
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.4 }}
                        className="bg-white/10 backdrop-blur rounded-2xl p-4 text-center min-w-[120px]"
                      >
                        <p className="text-white/60 text-sm mb-1">Risk Level</p>
                        <p className="text-4xl font-black text-white">{riskLevel}</p>
                      </motion.div>
                    )}
                    {defaultProb !== null && (
                      <motion.div 
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.5 }}
                        className="bg-white/10 backdrop-blur rounded-2xl p-4 text-center min-w-[120px]"
                      >
                        <p className="text-white/60 text-sm mb-1">Default Prob.</p>
                        <p className="text-4xl font-black text-white">{formatPercent(defaultProb)}</p>
                      </motion.div>
                    )}
                    <motion.div 
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.6 }}
                      className="bg-white/10 backdrop-blur rounded-2xl p-4 text-center min-w-[120px]"
                    >
                      <p className="text-white/60 text-sm mb-1">Time</p>
                      <p className="text-4xl font-black text-white">{(elapsedTime / 1000).toFixed(1)}s</p>
                    </motion.div>
                  </div>
                </div>
                
                {/* Approved Loan Terms */}
                {decisionType === 'APPROVE' && decisionData.loan_terms && (
                  <motion.div 
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.7 }}
                    className="mt-8 pt-8 border-t border-white/20"
                  >
                    <h3 className="text-2xl font-bold text-white mb-4 flex items-center">
                      <BanknotesIcon className="w-7 h-7 mr-2" /> Approved Loan Terms
                    </h3>
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
                      <div>
                        <p className="text-white/60 text-sm">Amount</p>
                        <p className="text-3xl font-black text-white">
                          {formatCurrency(decisionData.loan_terms.approved_amount || 0)}
                        </p>
                      </div>
                      <div>
                        <p className="text-white/60 text-sm">Interest Rate</p>
                        <p className="text-3xl font-black text-white">
                          {formatPercent(decisionData.loan_terms.interest_rate || 0)} <span className="text-lg font-normal">APR</span>
                        </p>
                      </div>
                      <div>
                        <p className="text-white/60 text-sm">Term</p>
                        <p className="text-3xl font-black text-white">
                          {decisionData.loan_terms.term_months || 0} <span className="text-lg font-normal">months</span>
                        </p>
                      </div>
                      <div>
                        <p className="text-white/60 text-sm">Monthly Payment</p>
                        <p className="text-3xl font-black text-white">
                          {formatCurrency(decisionData.loan_terms.monthly_payment || 0)}
                        </p>
                      </div>
                    </div>
                  </motion.div>
                )}
              </div>

              {/* Applicant Summary Section */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.35 }}
                className="bg-slate-800/50 backdrop-blur rounded-2xl border border-slate-700 p-6 mb-8"
              >
                <h3 className="text-xl font-bold text-white mb-4 flex items-center">
                  <IdentificationIcon className="w-6 h-6 mr-2 text-cyan-400" /> Applicant Summary
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                  <div className="bg-slate-900/50 rounded-xl p-3">
                    <div className="flex items-center mb-1">
                      <UserIcon className="w-4 h-4 text-slate-500 mr-1" />
                      <p className="text-xs text-slate-500">Applicant</p>
                    </div>
                    <p className="text-white font-semibold truncate">
                      {applicationData?.applicant?.name || 'N/A'}
                    </p>
                  </div>
                  <div className="bg-slate-900/50 rounded-xl p-3">
                    <div className="flex items-center mb-1">
                      <BanknotesIcon className="w-4 h-4 text-slate-500 mr-1" />
                      <p className="text-xs text-slate-500">Loan Amount</p>
                    </div>
                    <p className="text-white font-semibold">
                      {formatCurrency(applicationData?.loan?.amount || 0)}
                    </p>
                  </div>
                  <div className="bg-slate-900/50 rounded-xl p-3">
                    <div className="flex items-center mb-1">
                      <ChartBarIcon className="w-4 h-4 text-slate-500 mr-1" />
                      <p className="text-xs text-slate-500">Credit Score</p>
                    </div>
                    <p className={`font-semibold ${
                      (applicationData?.credit?.credit_score || 0) >= 740 ? 'text-green-400' :
                      (applicationData?.credit?.credit_score || 0) >= 670 ? 'text-amber-400' :
                      'text-red-400'
                    }`}>
                      {applicationData?.credit?.credit_score || 'N/A'}
                    </p>
                  </div>
                  <div className="bg-slate-900/50 rounded-xl p-3">
                    <div className="flex items-center mb-1">
                      <CurrencyDollarIcon className="w-4 h-4 text-slate-500 mr-1" />
                      <p className="text-xs text-slate-500">Annual Income</p>
                    </div>
                    <p className="text-white font-semibold">
                      {formatCurrency(applicationData?.employment?.annual_income || 0)}
                    </p>
                  </div>
                  <div className="bg-slate-900/50 rounded-xl p-3">
                    <div className="flex items-center mb-1">
                      <BriefcaseIcon className="w-4 h-4 text-slate-500 mr-1" />
                      <p className="text-xs text-slate-500">Employment</p>
                    </div>
                    <p className="text-white font-semibold capitalize truncate">
                      {applicationData?.employment?.status?.replace('_', ' ') || 'N/A'}
                    </p>
                  </div>
                  <div className="bg-slate-900/50 rounded-xl p-3">
                    <div className="flex items-center mb-1">
                      <ScaleIcon className="w-4 h-4 text-slate-500 mr-1" />
                      <p className="text-xs text-slate-500">DTI Ratio</p>
                    </div>
                    <p className={`font-semibold ${
                      ((applicationData?.financial?.monthly_debt || 0) / ((applicationData?.employment?.annual_income || 1) / 12) * 100) <= 36 ? 'text-green-400' :
                      ((applicationData?.financial?.monthly_debt || 0) / ((applicationData?.employment?.annual_income || 1) / 12) * 100) <= 43 ? 'text-amber-400' :
                      'text-red-400'
                    }`}>
                      {applicationData?.employment?.annual_income 
                        ? `${((applicationData?.financial?.monthly_debt || 0) / (applicationData.employment.annual_income / 12) * 100).toFixed(1)}%`
                        : 'N/A'}
                    </p>
                  </div>
                </div>
              </motion.div>

              {/* Charts Section */}
              <div className="grid lg:grid-cols-2 gap-6 mb-8">
                {/* Agent Confidence Radar */}
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.4 }}
                  className="bg-slate-800/50 backdrop-blur rounded-2xl border border-slate-700 p-6"
                >
                  <h3 className="text-xl font-bold text-white mb-4 flex items-center">
                    <ChartBarIcon className="w-6 h-6 mr-2 text-blue-400" /> Agent Confidence Scores
                  </h3>
                  {radarData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={350}>
                      <RadarChart data={radarData}>
                        <PolarGrid stroke="#475569" />
                        <PolarAngleAxis dataKey="agent" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                        <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#64748b' }} />
                        <Radar
                          name="Confidence"
                          dataKey="confidence"
                          stroke="#3b82f6"
                          fill="#3b82f6"
                          fillOpacity={0.4}
                        />
                      </RadarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-[350px] flex items-center justify-center text-slate-500">
                      <p>Loading confidence data...</p>
                    </div>
                  )}
                </motion.div>

                {/* Risk Distribution Comparison Chart */}
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.5 }}
                  className="bg-slate-800/50 backdrop-blur rounded-2xl border border-slate-700 p-6"
                >
                  <h3 className="text-xl font-bold text-white mb-2 flex items-center">
                    <ArrowTrendingUpIcon className="w-6 h-6 mr-2 text-amber-400" /> Risk Distribution vs All Applicants
                  </h3>
                  <p className="text-slate-400 text-sm mb-4">
                    {riskPercentile !== null ? (
                      <>
                        Your application ranks at the <span className={`font-bold ${riskStyle.color}`}>{riskPercentile}th percentile</span> across all applicants
                        {riskPercentile <= 25 && <span className="text-green-400 ml-1">(Lower risk than {100 - riskPercentile}% of applicants)</span>}
                        {riskPercentile > 25 && riskPercentile <= 50 && <span className="text-blue-400 ml-1">(Below median risk)</span>}
                        {riskPercentile > 50 && riskPercentile <= 75 && <span className="text-amber-400 ml-1">(Above median risk)</span>}
                        {riskPercentile > 75 && <span className="text-red-400 ml-1">(Higher risk than {riskPercentile}% of applicants)</span>}
                      </>
                    ) : (
                      <span className="text-slate-500">Calculating risk percentile...</span>
                    )}
                  </p>
                  <ResponsiveContainer width="100%" height={300}>
                    <AreaChart data={distributionData}>
                      <defs>
                        <linearGradient id="riskGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor={riskStyle.chartColor} stopOpacity={0.8}/>
                          <stop offset="95%" stopColor={riskStyle.chartColor} stopOpacity={0.1}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis 
                        dataKey="x" 
                        tick={{ fill: '#94a3b8', fontSize: 10 }} 
                        label={{ value: 'Default Probability %', position: 'bottom', fill: '#64748b', offset: -5 }}
                      />
                      <YAxis 
                        tick={{ fill: '#94a3b8' }} 
                        label={{ value: 'Applications', angle: -90, position: 'insideLeft', fill: '#64748b' }} 
                      />
                      <Tooltip 
                        contentStyle={{ background: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }}
                        labelStyle={{ color: '#e2e8f0' }}
                        formatter={(value: any) => [`${Math.round(value)} applications`, 'Count']}
                        labelFormatter={(label: any) => `Default Prob: ${label}%`}
                      />
                      <Area
                        type="monotone"
                        dataKey="count"
                        stroke={riskStyle.chartColor}
                        strokeWidth={2}
                        fill="url(#riskGradient)"
                      />
                      {applicantX !== null && applicantY !== null && (
                        <ReferenceDot 
                          x={applicantX} 
                          y={applicantY} 
                          r={10} 
                          fill="#fbbf24" 
                          stroke="#ffffff"
                          strokeWidth={3}
                        />
                      )}
                    </AreaChart>
                  </ResponsiveContainer>
                  <div className="flex items-center justify-center mt-2 text-sm">
                    <div className="flex items-center mr-4">
                      <div className={`w-3 h-3 rounded ${riskStyle.bg} mr-1`}></div>
                      <span className="text-slate-400">{riskLevel} Risk Distribution</span>
                    </div>
                    <div className="flex items-center">
                      <div className="w-4 h-4 rounded-full bg-amber-400 border-2 border-white mr-1"></div>
                      <span className="text-amber-400 font-medium">Your Position</span>
                    </div>
                  </div>
                </motion.div>
              </div>

              {/* Risk & Mitigating Factors */}
              <div className="grid lg:grid-cols-2 gap-6 mb-8">
                {/* Risk Factors */}
                {decisionData.risk_assessment?.primary_risk_factors?.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.6 }}
                    className="bg-slate-800/50 backdrop-blur rounded-2xl border border-red-500/30 p-6"
                  >
                    <h3 className="text-xl font-bold text-red-400 mb-4 flex items-center">
                      <ExclamationTriangleIcon className="w-6 h-6 mr-2" /> Risk Factors Identified
                    </h3>
                    <ul className="space-y-2">
                      {decisionData.risk_assessment.primary_risk_factors.map((factor: string, i: number) => (
                        <motion.li 
                          key={i} 
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: 0.7 + i * 0.05 }}
                          className="flex items-start text-slate-300 bg-red-500/10 rounded-lg px-3 py-2"
                        >
                          <span className="text-red-400 mr-2 mt-0.5">▸</span>
                          {factor}
                        </motion.li>
                      ))}
                    </ul>
                  </motion.div>
                )}

                {/* Mitigating Factors */}
                {decisionData.risk_assessment?.mitigating_factors?.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.7 }}
                    className="bg-slate-800/50 backdrop-blur rounded-2xl border border-green-500/30 p-6"
                  >
                    <h3 className="text-xl font-bold text-green-400 mb-4 flex items-center">
                      <CheckCircleIcon className="w-6 h-6 mr-2" /> Mitigating Factors
                    </h3>
                    <ul className="space-y-2">
                      {decisionData.risk_assessment.mitigating_factors.map((factor: string, i: number) => (
                        <motion.li 
                          key={i}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: 0.8 + i * 0.05 }}
                          className="flex items-start text-slate-300 bg-green-500/10 rounded-lg px-3 py-2"
                        >
                          <span className="text-green-400 mr-2 mt-0.5">▸</span>
                          {factor}
                        </motion.li>
                      ))}
                    </ul>
                  </motion.div>
                )}
              </div>

              {/* Customer Explanation */}
              {decisionData.customer_explanation && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.8 }}
                  className="bg-slate-800/50 backdrop-blur rounded-2xl border border-blue-500/30 p-6 mb-8"
                >
                  <h3 className="text-xl font-bold text-blue-400 mb-4 flex items-center">
                    <LightBulbIcon className="w-6 h-6 mr-2" /> Decision Explanation
                  </h3>
                  <p className="text-slate-300 text-lg leading-relaxed whitespace-pre-line">
                    {decisionData.customer_explanation}
                  </p>
                </motion.div>
              )}

              {/* Confidence Breakdown */}
              {decisionData.confidence_breakdown && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.9 }}
                  className="bg-slate-800/50 backdrop-blur rounded-2xl border border-slate-700 p-6 mb-8"
                >
                  <h3 className="text-xl font-bold text-white mb-2 flex items-center">
                    <CalculatorIcon className="w-6 h-6 mr-2 text-purple-400" /> Weighted Confidence Calculation
                  </h3>
                  <p className="text-slate-400 text-sm mb-4">
                    Final score calculated using weighted average: QuantRisk (25%) + Fraud (20%) + Credit (20%) + Income (15%) + Compliance (10%) + Collateral (5%) + Market (5%)
                  </p>
                  <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
                    {Object.entries(decisionData.confidence_breakdown).map(([agent, data]: [string, any]) => (
                      <div key={agent} className="bg-slate-900/50 rounded-xl p-3 text-center border border-slate-700">
                        <p className="text-xs text-slate-500 mb-1 truncate">{agent}</p>
                        <p className="text-xl font-bold text-white">{formatPercent(data.confidence)}</p>
                        <p className="text-xs text-purple-400">×{data.weight}</p>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}

              {/* New Application Button */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 1 }}
                className="text-center"
              >
                <a
                  href="/apply"
                  className="inline-flex items-center px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold rounded-full hover:from-blue-700 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl"
                >
                  <DocumentTextIcon className="w-5 h-5 mr-2" /> Start New Application
                </a>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Error State */}
        {error && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-red-900/50 border border-red-500 rounded-2xl p-8 text-center"
          >
            <XCircleIcon className="w-16 h-16 text-red-400 mx-auto mb-4" />
            <h3 className="text-2xl font-bold text-red-400 mb-2">Processing Error</h3>
            <p className="text-slate-300 mb-6">{error}</p>
            <a
              href="/apply"
              className="inline-flex items-center px-6 py-3 bg-red-600 text-white font-bold rounded-lg hover:bg-red-700 transition-colors"
            >
              Try Again
            </a>
          </motion.div>
        )}
      </div>
    </div>
  );
}
