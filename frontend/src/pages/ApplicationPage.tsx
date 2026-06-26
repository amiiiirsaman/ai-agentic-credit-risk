import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm, SubmitHandler } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { motion } from 'framer-motion';
import { useAppDispatch, useAppSelector } from '../store/store';
import { submitApplicationAsync, loadSyntheticApplication } from '../store/applicationSlice';
import { RiskProfile } from '../types';

// Schema matching backend LoanApplicationRequest model
const applicationSchema = z.object({
  // Applicant Info (matches ApplicantInfo)
  name: z.string().min(2, 'Full name is required'),
  email: z.string().email('Invalid email address'),
  phone: z.string().min(10, 'Phone number is required'),
  age: z.coerce.number().min(18, 'Must be at least 18').max(120),
  ssn_last_four: z.string().regex(/^\d{4}$/, 'Must be 4 digits').optional().or(z.literal('')),
  
  // Employment (matches EmploymentInfo)
  employmentStatus: z.string(),
  employer_name: z.string().optional().or(z.literal('')),
  job_title: z.string().optional().or(z.literal('')),
  years_employed: z.coerce.number().min(0),
  annual_income: z.coerce.number().min(0, 'Annual income must be positive'),
  
  // Credit (matches CreditInfo)
  credit_score: z.coerce.number().min(300).max(850),
  years_credit_history: z.coerce.number().min(0),
  num_credit_lines: z.coerce.number().min(0),
  credit_utilization: z.coerce.number().min(0).max(100),
  
  // Financial (matches FinancialInfo)
  monthly_debt: z.coerce.number().min(0),
  savings: z.coerce.number().min(0),
  
  // Loan Details (matches LoanDetails)
  loanPurpose: z.string().min(1, 'Loan purpose is required'),
  loanAmount: z.coerce.number().min(1000, 'Minimum loan amount is $1,000'),
  loanTerm: z.coerce.number().min(6).max(360),
  
  // Collateral
  collateralType: z.string().optional().or(z.literal('')),
  collateralValue: z.coerce.number().optional(),
});

type ApplicationFormData = z.infer<typeof applicationSchema>;

const steps = [
  { id: 1, title: 'Personal Information', fields: ['name', 'email', 'phone', 'age', 'ssn_last_four'] },
  { id: 2, title: 'Employment & Income', fields: ['employmentStatus', 'employer_name', 'job_title', 'years_employed', 'annual_income'] },
  { id: 3, title: 'Credit & Financial', fields: ['credit_score', 'years_credit_history', 'num_credit_lines', 'credit_utilization', 'monthly_debt', 'savings'] },
  { id: 4, title: 'Loan Details', fields: ['loanPurpose', 'loanAmount', 'loanTerm'] },
  { id: 5, title: 'Collateral', fields: ['collateralType', 'collateralValue'] },
];

export default function ApplicationPage() {
  const [currentStep, setCurrentStep] = useState(1);
  const [selectedRiskProfile, setSelectedRiskProfile] = useState<RiskProfile>(RiskProfile.MEDIUM);
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { isSubmitting: loading, error } = useAppSelector((state) => state.application);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
    trigger,
  } = useForm<ApplicationFormData>({
    resolver: zodResolver(applicationSchema),
    mode: 'onChange',
    defaultValues: {
      employmentStatus: 'employed',
      loanPurpose: 'personal',
      loanTerm: 60,
      monthly_debt: 0,
      savings: 0,
      years_credit_history: 5,
      num_credit_lines: 3,
      credit_utilization: 30,
      years_employed: 2,
      age: 35,
      credit_score: 700,
      annual_income: 75000,
      loanAmount: 25000,
    },
  });

  const handleGenerateSynthetic = async () => {
    try {
      const result = await dispatch(loadSyntheticApplication(selectedRiskProfile));
      if (loadSyntheticApplication.fulfilled.match(result)) {
        const data = result.payload;
        // Map synthetic data to form fields - matching backend structure
        if (data.applicant) {
          setValue('name', data.applicant.name || '');
          setValue('email', data.applicant.email || '');
          setValue('phone', data.applicant.phone?.replace('+1', '') || '');
          setValue('age', data.applicant.age || 35);
          setValue('ssn_last_four', data.applicant.ssn_last_four || '');
        }
        if (data.employment) {
          setValue('employmentStatus', data.employment.status || 'employed');
          setValue('employer_name', data.employment.employer_name || '');
          setValue('job_title', data.employment.job_title || '');
          setValue('years_employed', data.employment.years_employed || 0);
          setValue('annual_income', data.employment.annual_income || 0);
        }
        if (data.credit) {
          setValue('credit_score', data.credit.credit_score || 700);
          setValue('years_credit_history', data.credit.years_credit_history || 5);
          setValue('num_credit_lines', data.credit.num_credit_lines || 3);
          setValue('credit_utilization', data.credit.credit_utilization || 30);
        }
        if (data.financial) {
          setValue('monthly_debt', data.financial.monthly_debt || 0);
          setValue('savings', data.financial.savings || 0);
        }
        if (data.loan) {
          setValue('loanPurpose', data.loan.purpose || 'personal');
          setValue('loanAmount', data.loan.amount || 25000);
          setValue('loanTerm', data.loan.term_months || 60);
          setValue('collateralType', data.loan.collateral_type || '');
          setValue('collateralValue', data.loan.collateral_value || 0);
        }
        trigger();
      }
    } catch (err) {
      console.error('Failed to load synthetic data:', err);
    }
  };

  const handleNext = async () => {
    const currentFields = steps[currentStep - 1].fields;
    const isStepValid = await trigger(currentFields as any);
    if (isStepValid && currentStep < steps.length) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const onSubmit: SubmitHandler<ApplicationFormData> = async (data) => {
    // Transform form data to match backend LoanApplicationRequest structure
    const applicationData = {
      applicant: {
        name: data.name,
        email: data.email,
        phone: data.phone.startsWith('+') ? data.phone : `+1${data.phone.replace(/\D/g, '')}`,
        age: data.age,
        ssn_last_four: data.ssn_last_four || undefined,
      },
      loan: {
        amount: data.loanAmount,
        purpose: data.loanPurpose,
        term_months: data.loanTerm,
        collateral_type: data.collateralType || undefined,
        collateral_value: data.collateralValue || undefined,
      },
      employment: {
        status: data.employmentStatus,
        employer_name: data.employer_name || undefined,
        job_title: data.job_title || undefined,
        years_employed: data.years_employed,
        annual_income: data.annual_income,
      },
      credit: {
        credit_score: data.credit_score,
        years_credit_history: data.years_credit_history,
        num_credit_lines: data.num_credit_lines,
        credit_utilization: data.credit_utilization,
        delinquencies_2yrs: 0,
        public_records: 0,
        hard_inquiries_6mo: 0,
      },
      financial: {
        monthly_debt: data.monthly_debt,
        savings: data.savings,
        checking_balance: 0,
        investment_accounts: 0,
        other_income: 0,
      },
      documents: [],
    };

    const result = await dispatch(submitApplicationAsync(applicationData as any));
    if (submitApplicationAsync.fulfilled.match(result)) {
      navigate(`/decision/${result.payload.application_id}`);
    }
  };

  // Helper to get error message as string
  const getErrorMessage = (err: any): string => {
    if (!err) return '';
    if (typeof err === 'string') return err;
    if (err.message) return err.message;
    if (Array.isArray(err)) return err.map((e: any) => e.msg || e.message || JSON.stringify(e)).join(', ');
    return JSON.stringify(err);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <h1 className="font-display text-3xl font-bold text-gray-900 mb-2">
            Loan Application
          </h1>
          <p className="text-gray-600">
            Complete the form below to submit your application for AI-powered analysis
          </p>
        </motion.div>

        {/* Synthetic Data Generator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="bg-yellow-50 border border-yellow-200 rounded-xl p-6 mb-8"
        >
          <h3 className="font-semibold text-yellow-800 mb-3 flex items-center">
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
            </svg>
            Demo Mode: Generate Synthetic Data
          </h3>
          <p className="text-sm text-yellow-700 mb-4">
            Select a risk profile to auto-fill the form with realistic test data
          </p>
          <div className="flex flex-wrap items-center gap-4">
            <select
              value={selectedRiskProfile}
              onChange={(e) => setSelectedRiskProfile(e.target.value as RiskProfile)}
              className="px-4 py-2 border border-yellow-300 rounded-lg bg-white text-gray-800 focus:ring-2 focus:ring-yellow-500"
            >
              <option value={RiskProfile.LOW}>Low Risk</option>
              <option value={RiskProfile.MEDIUM}>Medium Risk</option>
              <option value={RiskProfile.HIGH}>High Risk</option>
            </select>
            <button
              type="button"
              onClick={handleGenerateSynthetic}
              className="px-6 py-2 bg-yellow-500 text-white font-medium rounded-lg hover:bg-yellow-600 transition-colors"
            >
              Generate Data
            </button>
          </div>
        </motion.div>

        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            {steps.map((step, index) => (
              <div key={step.id} className="flex items-center">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold text-sm ${
                    currentStep >= step.id
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-200 text-gray-500'
                  }`}
                >
                  {currentStep > step.id ? (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    step.id
                  )}
                </div>
                {index < steps.length - 1 && (
                  <div
                    className={`w-full h-1 mx-2 ${
                      currentStep > step.id ? 'bg-blue-600' : 'bg-gray-200'
                    }`}
                    style={{ width: '60px' }}
                  />
                )}
              </div>
            ))}
          </div>
          <div className="flex justify-between mt-2">
            {steps.map((step) => (
              <span
                key={step.id}
                className={`text-xs ${
                  currentStep >= step.id ? 'text-blue-600' : 'text-gray-400'
                }`}
              >
                {step.title}
              </span>
            ))}
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)}>
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="bg-white rounded-xl shadow-lg p-8"
          >
            <h2 className="font-display text-xl font-bold text-gray-900 mb-6">
              {steps[currentStep - 1].title}
            </h2>

            {/* Step 1: Personal Information */}
            {currentStep === 1 && (
              <div className="grid md:grid-cols-2 gap-6">
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                  <input
                    type="text"
                    {...register('name')}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="John Smith"
                  />
                  {errors.name && <p className="text-red-500 text-sm mt-1">{errors.name.message}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                  <input
                    type="email"
                    {...register('email')}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="john@example.com"
                  />
                  {errors.email && <p className="text-red-500 text-sm mt-1">{errors.email.message}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                  <input
                    type="tel"
                    {...register('phone')}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="5551234567"
                  />
                  {errors.phone && <p className="text-red-500 text-sm mt-1">{errors.phone.message}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Age</label>
                  <input
                    type="number"
                    {...register('age')}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="35"
                  />
                  {errors.age && <p className="text-red-500 text-sm mt-1">{errors.age.message}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">SSN Last 4 (Optional)</label>
                  <input
                    type="text"
                    maxLength={4}
                    {...register('ssn_last_four')}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="1234"
                  />
                  {errors.ssn_last_four && <p className="text-red-500 text-sm mt-1">{errors.ssn_last_four.message}</p>}
                </div>
              </div>
            )}

            {/* Step 2: Employment */}
            {currentStep === 2 && (
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Employment Status</label>
                  <select
                    {...register('employmentStatus')}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="employed">Employed</option>
                    <option value="self_employed">Self-Employed</option>
                    <option value="unemployed">Unemployed</option>
                    <option value="retired">Retired</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Employer Name</label>
                  <input
                    type="text"
                    {...register('employer_name')}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Company Inc."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Job Title</label>
                  <input
                    type="text"
                    {...register('job_title')}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Software Engineer"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Years Employed</label>
                  <input
                    type="number"
                    step="0.5"
                    {...register('years_employed')}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="5"
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Annual Income ($)</label>
                  <input
                    type="number"
                    {...register('annual_income')}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="75000"
                  />
                  {errors.annual_income && <p className="text-red-500 text-sm mt-1">{errors.annual_income.message}</p>}
                </div>
              </div>
            )}

            {/* Step 3: Credit & Financial */}
            {currentStep === 3 && (
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Credit Score (300-850)</label>
                  <input
                    type="number"
                    min={300}
                    max={850}
                    {...register('credit_score')}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="720"
                  />
                  {errors.credit_score && <p className="text-red-500 text-sm mt-1">{errors.credit_score.message}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Years of Credit History</label>
                  <input
                    type="number"
                    step="0.5"
                    {...register('years_credit_history')}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="8"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Number of Credit Lines</label>
                  <input
                    type="number"
                    {...register('num_credit_lines')}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="4"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Credit Utilization (%)</label>
                  <input
                    type="number"
                    min={0}
                    max={100}
                    {...register('credit_utilization')}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="25"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Monthly Debt ($)</label>
                  <input
                    type="number"
                    {...register('monthly_debt')}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Savings ($)</label>
                  <input
                    type="number"
                    {...register('savings')}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="10000"
                  />
                </div>
              </div>
            )}

            {/* Step 4: Loan Details */}
            {currentStep === 4 && (
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Loan Purpose</label>
                  <select
                    {...register('loanPurpose')}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="personal">Personal Loan</option>
                    <option value="home_purchase">Home Purchase</option>
                    <option value="refinance">Refinance</option>
                    <option value="auto">Auto Loan</option>
                    <option value="business">Business Loan</option>
                    <option value="education">Education</option>
                    <option value="debt_consolidation">Debt Consolidation</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Loan Amount ($)</label>
                  <input
                    type="number"
                    {...register('loanAmount')}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="25000"
                  />
                  {errors.loanAmount && <p className="text-red-500 text-sm mt-1">{errors.loanAmount.message}</p>}
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Loan Term (months)</label>
                  <input
                    type="number"
                    min={6}
                    max={360}
                    {...register('loanTerm')}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="60"
                  />
                </div>
              </div>
            )}

            {/* Step 5: Collateral */}
            {currentStep === 5 && (
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Collateral Type (Optional)</label>
                  <select
                    {...register('collateralType')}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">None</option>
                    <option value="real_estate">Real Estate</option>
                    <option value="vehicle">Vehicle</option>
                    <option value="savings">Savings Account</option>
                    <option value="investments">Investments</option>
                    <option value="equipment">Equipment</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Collateral Value ($)</label>
                  <input
                    type="number"
                    {...register('collateralValue')}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="50000"
                  />
                </div>
              </div>
            )}

            {/* Error Display */}
            {error && (
              <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                {getErrorMessage(error)}
              </div>
            )}

            {/* Navigation */}
            <div className="mt-8 flex justify-between">
              <button
                type="button"
                onClick={handlePrevious}
                disabled={currentStep === 1}
                className="px-6 py-2 text-gray-600 font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:text-gray-800 transition-colors"
              >
                Previous
              </button>
              {currentStep < steps.length ? (
                <button
                  type="button"
                  onClick={handleNext}
                  className="px-6 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Next
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={loading}
                  className="px-8 py-3 bg-green-500 text-white font-bold rounded-lg hover:bg-green-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                >
                  {loading ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-3 h-5 w-5" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      Processing...
                    </>
                  ) : (
                    'Submit Application'
                  )}
                </button>
              )}
            </div>
          </motion.div>
        </form>
      </div>
    </div>
  );
}
