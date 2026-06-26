import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import type { LoanApplication, ApplicationResponse, ApplicationStatusResponse } from '../types';
import { submitApplication, getApplicationStatus, getSyntheticApplication } from '../utils/api';

interface ApplicationState {
  currentApplication: Partial<LoanApplication> | null;
  applicationId: string | null;
  status: ApplicationStatusResponse | null;
  isSubmitting: boolean;
  isLoading: boolean;
  error: string | null;
  currentStep: number;
}

const initialState: ApplicationState = {
  currentApplication: null,
  applicationId: null,
  status: null,
  isSubmitting: false,
  isLoading: false,
  error: null,
  currentStep: 0,
};

// Async thunks
export const submitApplicationAsync = createAsyncThunk(
  'application/submit',
  async (application: LoanApplication, { rejectWithValue }) => {
    try {
      const response = await submitApplication(application);
      return response;
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      return rejectWithValue(err.response?.data?.detail || 'Failed to submit application');
    }
  }
);

export const fetchApplicationStatus = createAsyncThunk(
  'application/fetchStatus',
  async (applicationId: string, { rejectWithValue }) => {
    try {
      const response = await getApplicationStatus(applicationId);
      return response;
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      return rejectWithValue(err.response?.data?.detail || 'Failed to fetch status');
    }
  }
);

export const loadSyntheticApplication = createAsyncThunk(
  'application/loadSynthetic',
  async (riskProfile: string = 'random', { rejectWithValue }) => {
    try {
      const response = await getSyntheticApplication(riskProfile);
      return response;
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      return rejectWithValue(err.response?.data?.detail || 'Failed to load synthetic data');
    }
  }
);

const applicationSlice = createSlice({
  name: 'application',
  initialState,
  reducers: {
    setCurrentApplication: (state, action: PayloadAction<Partial<LoanApplication>>) => {
      state.currentApplication = { ...state.currentApplication, ...action.payload };
    },
    setCurrentStep: (state, action: PayloadAction<number>) => {
      state.currentStep = action.payload;
    },
    nextStep: (state) => {
      state.currentStep += 1;
    },
    prevStep: (state) => {
      state.currentStep = Math.max(0, state.currentStep - 1);
    },
    resetApplication: (state) => {
      state.currentApplication = null;
      state.applicationId = null;
      state.status = null;
      state.error = null;
      state.currentStep = 0;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Submit application
      .addCase(submitApplicationAsync.pending, (state) => {
        state.isSubmitting = true;
        state.error = null;
      })
      .addCase(submitApplicationAsync.fulfilled, (state, action) => {
        state.isSubmitting = false;
        state.applicationId = action.payload.application_id;
      })
      .addCase(submitApplicationAsync.rejected, (state, action) => {
        state.isSubmitting = false;
        state.error = action.payload as string;
      })
      // Fetch status
      .addCase(fetchApplicationStatus.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(fetchApplicationStatus.fulfilled, (state, action) => {
        state.isLoading = false;
        state.status = action.payload;
      })
      .addCase(fetchApplicationStatus.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Load synthetic
      .addCase(loadSyntheticApplication.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(loadSyntheticApplication.fulfilled, (state, action) => {
        state.isLoading = false;
        state.currentApplication = action.payload;
      })
      .addCase(loadSyntheticApplication.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });
  },
});

export const {
  setCurrentApplication,
  setCurrentStep,
  nextStep,
  prevStep,
  resetApplication,
  clearError,
} = applicationSlice.actions;

export default applicationSlice.reducer;
