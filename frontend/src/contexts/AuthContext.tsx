import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { User, Hotel, LoginRequest, SignupRequest } from '@/types/api';
import { authApi } from '@/api/auth';
import { apiClient, tokenStorage } from '@/api/client';
import { supabase } from '@/lib/supabase';

interface AuthContextType {
  user: User | null;
  hotel: Hotel | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  signup: (data: SignupRequest) => Promise<void>;
  logout: () => Promise<void>;
  setHotel: (hotel: Hotel) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [hotel, setHotel] = useState<Hotel | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSigningUp, setIsSigningUp] = useState(false);

  // Sync session state with Supabase
  useEffect(() => {
    const initAuth = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      
      if (session) {
        tokenStorage.setTokens({
          access_token: session.access_token,
          refresh_token: session.refresh_token || '',
          token_type: 'Bearer',
          expires_in: session.expires_in || 3600,
        });
        
        try {
          const currentUser = await authApi.getCurrentUser();
          setUser(currentUser);
          
          const hotelData = await apiClient.get<Hotel>('/hotels/me');
          setHotel(hotelData);
        } catch (error) {
          console.error('Error fetching user data:', error);
          if (session) await supabase.auth.signOut();
        }
      }
      setIsLoading(false);
    };

    initAuth();

    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, session) => {
      if (event === 'SIGNED_IN' && session) {
        // ALWAYS update tokens when signed in
        tokenStorage.setTokens({
          access_token: session.access_token,
          refresh_token: session.refresh_token || '',
          token_type: 'Bearer',
          expires_in: session.expires_in || 3600,
        });

        // If we are currently in the signup process, don't fetch user profile yet
        // The signup function will handle the initial data fetch
        if (isSigningUp) {
          console.log('Skipping profile fetch during signup sync');
          return;
        }

        try {
          const currentUser = await authApi.getCurrentUser();
          setUser(currentUser);
          
          const hotelData = await apiClient.get<Hotel>('/hotels/me');
          setHotel(hotelData);
        } catch (error) {
          console.error('Error fetching user data in auth state change:', error);
          // Only sign out if it's a persistent failure, not during signup
          if (!isSigningUp) await supabase.auth.signOut();
        }
      } else if (event === 'SIGNED_OUT') {
        setUser(null);
        setHotel(null);
        tokenStorage.clearTokens();
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  const login = useCallback(async (credentials: LoginRequest) => {
    setIsLoading(true);
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email: credentials.email,
        password: credentials.password,
      });

      if (error) throw error;
      if (!data.session) throw new Error('No session created');

      // tokenStorage logic is handled by onAuthStateChange
    } finally {
      setIsLoading(false);
    }
  }, []);

  const signup = useCallback(async (data: SignupRequest) => {
    setIsLoading(true);
    setIsSigningUp(true);
    try {
      // 1. Sign up with Supabase
      console.log('Starting Supabase signup...');
      const { data: authData, error: authError } = await supabase.auth.signUp({
        email: data.email,
        password: data.password,
        options: {
          data: {
            name: data.name,
            hotel_name: data.hotel_name,
          }
        }
      });

      if (authError) throw authError;
      if (!authData.user) throw new Error('Supabase signup failed - no user returned');
      console.log('Supabase signup success:', authData.user.id);

      // 2. Call backend to create profile
      console.log('Calling backend signup...');
      try {
        await authApi.signup({
          ...data,
          id: authData.user.id,
        });
        console.log('Backend signup success');
      } catch (backendError: any) {
        console.error('Backend signup failed:', backendError);
        // Even if backend fails, we might be able to proceed if lazy-create works on next fetch
        // But for now, let's throw to show error to user
        throw new Error(backendError.message || 'Hotel profile creation failed. Please try logging in.');
      }

      // 3. Fetch user profile
      try {
        const currentUser = await authApi.getCurrentUser();
        setUser(currentUser);
        
        const hotelData = await apiClient.get<Hotel>('/hotels/me');
        setHotel(hotelData);
      } catch (e) {
        console.log('Initial profile fetch failed, will retry on dashboard load');
      }

    } catch (error: any) {
      console.error('Signup process failed:', error);
      throw error; // Rethrow to be caught by the Signup page component
    } finally {
      setIsSigningUp(false);
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    setIsLoading(true);
    await supabase.auth.signOut();
    setIsLoading(false);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        hotel,
        isLoading,
        isAuthenticated: !!user,
        login,
        signup,
        logout,
        setHotel,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
