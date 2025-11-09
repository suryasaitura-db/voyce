import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient, formDataClient } from '../services/api';
import {
  Submission,
  SubmissionResponse,
  PaginationParams,
  AnalyticsData,
} from '../types';
import { API_ENDPOINTS, QUERY_KEYS } from '../utils/constants';

/**
 * Fetch all submissions
 */
export const useSubmissions = (params?: PaginationParams) => {
  return useQuery({
    queryKey: [QUERY_KEYS.SUBMISSIONS, params],
    queryFn: async () => {
      const response = await apiClient.get<Submission[]>(
        API_ENDPOINTS.SUBMISSIONS.LIST,
        { params }
      );
      return response.data;
    },
  });
};

/**
 * Fetch single submission by ID
 */
export const useSubmission = (id: string) => {
  return useQuery({
    queryKey: [QUERY_KEYS.SUBMISSION_DETAIL, id],
    queryFn: async () => {
      const response = await apiClient.get<Submission>(
        API_ENDPOINTS.SUBMISSIONS.GET(id)
      );
      return response.data;
    },
    enabled: !!id,
  });
};

/**
 * Create new submission
 */
export const useCreateSubmission = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (audioFile: File) => {
      const formData = new FormData();
      formData.append('audio_file', audioFile);

      const response = await formDataClient.post<SubmissionResponse>(
        API_ENDPOINTS.SUBMISSIONS.CREATE,
        formData
      );
      return response.data;
    },
    onSuccess: () => {
      // Invalidate submissions cache
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.SUBMISSIONS] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.ANALYTICS] });
    },
  });
};

/**
 * Delete submission
 */
export const useDeleteSubmission = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(API_ENDPOINTS.SUBMISSIONS.DELETE(id));
    },
    onSuccess: () => {
      // Invalidate submissions cache
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.SUBMISSIONS] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.ANALYTICS] });
    },
  });
};

/**
 * Fetch analytics data
 */
export const useAnalytics = () => {
  return useQuery({
    queryKey: [QUERY_KEYS.ANALYTICS],
    queryFn: async () => {
      const response = await apiClient.get<AnalyticsData>(
        API_ENDPOINTS.ANALYTICS.GET
      );
      return response.data;
    },
  });
};
