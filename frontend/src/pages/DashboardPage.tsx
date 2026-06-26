import { useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { useAppDispatch, useAppSelector } from '../store/store';
import { fetchDashboardMetrics } from '../store/decisionSlice';
import { formatCurrency, formatPercent, formatNumber } from '../utils/format';

// Mock data for demonstration
const mockTrendData = [
  { month: 'Jan', applications: 145, approved: 98, denied: 32, pending: 15 },
  { month: 'Feb', applications: 178, approved: 125, denied: 38, pending: 15 },
  { month: 'Mar', applications: 203, approved: 156, denied: 35, pending: 12 },
  { month: 'Apr', applications: 189, approved: 142, denied: 30, pending: 17 },
  { month: 'May', applications: 234, approved: 178, denied: 41, pending: 15 },
  { month: 'Jun', applications: 267, approved: 198, denied: 52, pending: 17 },
];

const mockAgentPerformance = [
  { agent: 'Chief Underwriter', avgTime: 2.3, accuracy: 0.96 },
  { agent: 'Quantitative Risk', avgTime: 1.8, accuracy: 0.94 },
  { agent: 'Fraud Detection', avgTime: 1.5, accuracy: 0.98 },
  { agent: 'Income Verification', avgTime: 1.2, accuracy: 0.95 },
  { agent: 'Credit History', avgTime: 1.4, accuracy: 0.97 },
  { agent: 'Compliance', avgTime: 0.8, accuracy: 0.99 },
  { agent: 'Collateral', avgTime: 1.1, accuracy: 0.93 },
  { agent: 'Market Conditions', avgTime: 0.9, accuracy: 0.91 },
];

const mockRiskDistribution = [
  { name: 'Low Risk', value: 45, color: '#10b981' },
  { name: 'Medium Risk', value: 35, color: '#f59e0b' },
  { name: 'High Risk', value: 15, color: '#ef4444' },
  { name: 'Very High', value: 5, color: '#7f1d1d' },
];

const mockLoanTypeData = [
  { type: 'Personal', count: 450, amount: 2250000 },
  { type: 'Mortgage', count: 120, amount: 36000000 },
  { type: 'Auto', count: 280, amount: 5600000 },
  { type: 'Business', count: 95, amount: 4750000 },
  { type: 'Student', count: 180, amount: 2700000 },
];

export default function DashboardPage() {
  const dispatch = useAppDispatch();
  const { dashboardMetrics: metrics } = useAppSelector((state: any) => state.decision);

  useEffect(() => {
    dispatch(fetchDashboardMetrics());
  }, [dispatch]);

  // Default metrics with fallback values
  const defaultMetrics = {
    total_applications: 1216,
    approved_count: 897,
    denied_count: 228,
    pending_count: 91,
    approval_rate: 0.737,
    avg_processing_time: 12.4,
    avg_confidence_score: 0.89,
    total_loan_amount: 51300000,
  };

  // Merge API metrics with defaults to ensure all properties exist
  const displayMetrics = {
    total_applications: metrics?.total_applications ?? defaultMetrics.total_applications,
    approved_count: metrics?.approved_count ?? defaultMetrics.approved_count,
    denied_count: metrics?.denied_count ?? defaultMetrics.denied_count,
    pending_count: metrics?.pending_count ?? defaultMetrics.pending_count,
    approval_rate: metrics?.approval_rate ?? defaultMetrics.approval_rate,
    avg_processing_time: metrics?.avg_processing_time ?? defaultMetrics.avg_processing_time,
    avg_confidence_score: metrics?.avg_confidence_score ?? defaultMetrics.avg_confidence_score,
    total_loan_amount: metrics?.total_loan_amount ?? defaultMetrics.total_loan_amount,
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="font-display text-3xl font-bold text-gray-900">
            Analytics Dashboard
          </h1>
          <p className="text-gray-600 mt-1">
            Real-time insights into your AI credit risk assessment platform
          </p>
        </motion.div>

        {/* KPI Cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8"
        >
          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Total Applications</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {formatNumber(displayMetrics.total_applications)}
                </p>
              </div>
              <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
            </div>
            <div className="mt-4 flex items-center text-sm">
              <span className="text-green-600 flex items-center">
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                </svg>
                12.5%
              </span>
              <span className="text-gray-500 ml-2">vs last month</span>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Approval Rate</p>
                <p className="text-2xl font-bold text-green-600 mt-1">
                  {formatPercent(displayMetrics.approval_rate)}
                </p>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
            </div>
            <div className="mt-4 flex items-center text-sm">
              <span className="text-green-600">{displayMetrics.approved_count}</span>
              <span className="text-gray-500 ml-1">approved</span>
              <span className="text-gray-300 mx-2">|</span>
              <span className="text-red-500">{displayMetrics.denied_count}</span>
              <span className="text-gray-500 ml-1">denied</span>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Avg Processing Time</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {displayMetrics.avg_processing_time.toFixed(1)}s
                </p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
            <div className="mt-4 flex items-center text-sm">
              <span className="text-green-600 flex items-center">
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                </svg>
                18%
              </span>
              <span className="text-gray-500 ml-2">faster than target</span>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Total Loan Volume</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {formatCurrency(displayMetrics.total_loan_amount)}
                </p>
              </div>
              <div className="w-12 h-12 bg-gold-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-gold-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
            <div className="mt-4 flex items-center text-sm">
              <span className="text-gray-500">Avg confidence:</span>
              <span className="text-primary-600 ml-1 font-medium">
                {formatPercent(displayMetrics.avg_confidence_score)}
              </span>
            </div>
          </div>
        </motion.div>

        {/* Charts Row 1 */}
        <div className="grid lg:grid-cols-2 gap-8 mb-8">
          {/* Application Trends */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white rounded-xl shadow-sm p-6"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Application Trends</h3>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={mockTrendData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="approved"
                  stackId="1"
                  stroke="#10b981"
                  fill="#10b981"
                  fillOpacity={0.6}
                  name="Approved"
                />
                <Area
                  type="monotone"
                  dataKey="denied"
                  stackId="1"
                  stroke="#ef4444"
                  fill="#ef4444"
                  fillOpacity={0.6}
                  name="Denied"
                />
                <Area
                  type="monotone"
                  dataKey="pending"
                  stackId="1"
                  stroke="#f59e0b"
                  fill="#f59e0b"
                  fillOpacity={0.6}
                  name="Pending"
                />
              </AreaChart>
            </ResponsiveContainer>
          </motion.div>

          {/* Risk Distribution */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-white rounded-xl shadow-sm p-6"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Risk Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={mockRiskDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {mockRiskDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </motion.div>
        </div>

        {/* Charts Row 2 */}
        <div className="grid lg:grid-cols-2 gap-8 mb-8">
          {/* Agent Performance */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 }}
            className="bg-white rounded-xl shadow-sm p-6"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Agent Performance</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={mockAgentPerformance} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" domain={[0, 3]} />
                <YAxis dataKey="agent" type="category" width={130} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(value: number) => `${value.toFixed(1)}s`} />
                <Legend />
                <Bar dataKey="avgTime" name="Avg Time (s)" fill="#1a3b5c" />
              </BarChart>
            </ResponsiveContainer>
          </motion.div>

          {/* Loan Type Distribution */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.5 }}
            className="bg-white rounded-xl shadow-sm p-6"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Loan Type Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={mockLoanTypeData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="type" />
                <YAxis yAxisId="left" orientation="left" stroke="#1a3b5c" />
                <YAxis yAxisId="right" orientation="right" stroke="#d4af37" />
                <Tooltip
                  formatter={(value: number, name: string) => {
                    if (name === 'Amount') return formatCurrency(value);
                    return value;
                  }}
                />
                <Legend />
                <Bar yAxisId="left" dataKey="count" name="Applications" fill="#1a3b5c" />
                <Bar yAxisId="right" dataKey="amount" name="Amount" fill="#d4af37" />
              </BarChart>
            </ResponsiveContainer>
          </motion.div>
        </div>

        {/* Agent Accuracy Table */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="bg-white rounded-xl shadow-sm p-6"
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Agent Accuracy Metrics</h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Agent</th>
                  <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">Avg Time</th>
                  <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">Accuracy</th>
                  <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">Status</th>
                </tr>
              </thead>
              <tbody>
                {mockAgentPerformance.map((agent, index) => (
                  <tr key={agent.agent} className={index % 2 === 0 ? 'bg-gray-50' : ''}>
                    <td className="py-3 px-4 font-medium text-gray-900">{agent.agent}</td>
                    <td className="text-center py-3 px-4 text-gray-600">{agent.avgTime.toFixed(1)}s</td>
                    <td className="text-center py-3 px-4">
                      <span className={`font-medium ${
                        agent.accuracy >= 0.95 ? 'text-green-600' :
                        agent.accuracy >= 0.90 ? 'text-yellow-600' : 'text-red-600'
                      }`}>
                        {formatPercent(agent.accuracy)}
                      </span>
                    </td>
                    <td className="text-center py-3 px-4">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        Active
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
