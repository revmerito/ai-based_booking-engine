// Auth API Service - Real Backend Connection
import { apiClient, tokenStorage } from './client';
import { AuthResponse, LoginRequest, SignupRequest, User } from '@/types/api';

export const authApi = {
  // Login uses JSON format
  login: async (credentials: LoginRequest): Promise<{ access_token: string; refresh_token: string; token_type: string; expires_in: number }> => {
    const response = await apiClient.post<{ access_token: string; refresh_token: string; token_type: string; expires_in: number }>('/auth/login', credentials);

    tokenStorage.setTokens({
      access_token: response.access_token,
      refresh_token: response.refresh_token,
      token_type: (response.token_type || 'Bearer') as 'Bearer',
      expires_in: response.expires_in || 1800,
    });
    return response;
  },

  signup: async (data: SignupRequest): Promise<{ user: User; message?: string }> => {
    const response = await apiClient.post<{
      user: User;
      message?: string;
    }>('/auth/signup', data);

    return response;
  },

  logout: async (): Promise<void> => {
    tokenStorage.clearTokens();
  },

  getCurrentUser: async (): Promise<User> => {
    return apiClient.get<User>('/users/me');
  },

  forgotPassword: async (email: string): Promise<{ message: string }> => {
    return apiClient.post('/auth/forgot-password', { email });
  },

  resetPassword: async (token: string, password: string): Promise<{ message: string }> => {
    return apiClient.post('/auth/reset-password', { token, new_password: password });
  },

  changePassword: async (currentPassword: string, newPassword: string): Promise<{ message: string }> => {
    return apiClient.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
  },
};

export default authApi;
