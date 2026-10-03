import React, { createContext, useState, useEffect, useCallback } from 'react';
import { storage } from '../utils/storage';
import { authApi } from '../api/authApi';

export const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(() => storage.getToken());
  const [user, setUser] = useState(() => storage.getUser());
  const [isLoading, setIsLoading] = useState(true);

  const logout = useCallback(() => {
    storage.clearAuth();
    setToken(null);
    setUser(null);
  }, []);

  // Validate token on startup
  useEffect(() => {
    let isMounted = true;

    const verifyAuth = async () => {
      const storedToken = storage.getToken();
      if (!storedToken) {
        if (isMounted) {
          setIsLoading(false);
        }
        return;
      }

      try {
        const response = await authApi.getCurrentUser();
        const resData = response.data || response;
        const userData = resData.user || resData;
        if (isMounted) {
          setUser(userData);
          setToken(storedToken);
          storage.setUser(userData);
        }
      } catch (err) {
        console.warn('Initial token verification failed:', err);
        if (isMounted) {
          logout();
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    verifyAuth();

    return () => {
      isMounted = false;
    };
  }, [logout]);

  const login = async (email, password) => {
    const response = await authApi.login({ email, password });
    
    // Extract token and user data from backend response format
    const resData = response.data || response;
    const jwtToken = resData.access_token || resData.token;
    const userData = resData.user;

    if (!jwtToken) {
      throw new Error('No access token received from server');
    }

    // Save to storage first so synchronous checks succeed
    storage.setToken(jwtToken);
    storage.setUser(userData);
    setToken(jwtToken);
    setUser(userData);

    return userData;
  };

  const register = async (name, email, password) => {
    const response = await authApi.register({ name, email, password });
    
    const resData = response.data || response;
    const jwtToken = resData.access_token || resData.token;
    const userData = resData.user;

    if (jwtToken && userData) {
      storage.setToken(jwtToken);
      storage.setUser(userData);
      setToken(jwtToken);
      setUser(userData);
    } else {
      // Fallback: automatically log in if token not returned directly
      return login(email, password);
    }

    return userData;
  };

  const activeToken = token || storage.getToken();
  const activeUser = user || storage.getUser();
  const isAuthenticated = !!activeToken && !!activeUser;

  const value = {
    user: activeUser,
    token: activeToken,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
