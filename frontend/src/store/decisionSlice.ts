import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import type { UnderwritingDecision, DashboardMetrics } from '../types';
import { getDecision, getDashboardMetrics } from '../utils/api';

interface DecisionState {
  currentDecision: UnderwritingDecision | null;
  dashboardMetrics: DashboardMetrics | null;
  isLoading: boolean;
  error: string | null;
}

const initialState: DecisionState = {
  currentDecision: null,
  dashboardMetrics: null,
  isLoading: false,
  error: null,
};

// Async thunks
export const fetchDecision = createAsyncThunk(
  'decision/fetch',
  async (applicationId: string, { rejectWithValue }) => {
    try {
      const response = await getDecision(applicationId);
      return response;
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string }; status?: number } };
      if (err.response?.status === 202) {
        return rejectWithValue('Application is still being processed');
      }
      return rejectWithValue(err.response?.data?.detail || 'Failed to fetch decision');
    }
  }
);

export const fetchDashboardMetrics = createAsyncThunk(
  'decision/fetchMetrics',
  async (_, { rejectWithValue }) => {
    try {
      const response = await getDashboardMetrics();
      return response;
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      return rejectWithValue(err.response?.data?.detail || 'Failed to fetch metrics');
    }
  }
);

const decisionSlice = createSlice({
  name: 'decision',
  initialState,
  reducers: {
    setCurrentDecision: (state, action: PayloadAction<UnderwritingDecision>) => {
      state.currentDecision = action.payload;
    },
    clearDecision: (state) => {
      state.currentDecision = null;
      state.error = null;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch decision
      .addCase(fetchDecision.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchDecision.fulfilled, (state, action) => {
        state.isLoading = false;
        state.currentDecision = action.payload;
      })
      .addCase(fetchDecision.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Fetch dashboard metrics
      .addCase(fetchDashboardMetrics.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(fetchDashboardMetrics.fulfilled, (state, action) => {
        state.isLoading = false;
        state.dashboardMetrics = action.payload;
      })
      .addCase(fetchDashboardMetrics.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });
  },
});

export const { setCurrentDecision, clearDecision, clearError } = decisionSlice.actions;

export default decisionSlice.reducer;
