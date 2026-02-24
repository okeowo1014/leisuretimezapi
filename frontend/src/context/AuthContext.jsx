import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { auth as authApi, profile as profileApi } from '../api/endpoints';
import toast from 'react-hot-toast';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem('user');
    return stored ? JSON.parse(stored) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem('auth_token'));
  const [loading, setLoading] = useState(false);

  const isAuthenticated = !!token;

  const login = async (email, password) => {
    setLoading(true);
    try {
      const { data } = await authApi.login({ email, password });
      localStorage.setItem('auth_token', data.token);
      const userData = {
        id: data.id,
        email: data.email,
        firstname: data.firstname,
        lastname: data.lastname,
        wallet: data.wallet,
        image: data.image,
      };
      localStorage.setItem('user', JSON.stringify(userData));
      setToken(data.token);
      setUser(userData);
      toast.success('Welcome back!');
      return data;
    } catch (err) {
      const msg = err.response?.data?.error || err.response?.data?.detail || 'Login failed';
      toast.error(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const register = async (formData) => {
    setLoading(true);
    try {
      const { data } = await authApi.register(formData);
      if (data.token) {
        localStorage.setItem('auth_token', data.token);
        const userData = {
          id: data.id,
          email: data.email,
          firstname: data.firstname,
          lastname: data.lastname,
          wallet: data.wallet,
          image: data.image,
        };
        localStorage.setItem('user', JSON.stringify(userData));
        setToken(data.token);
        setUser(userData);
      }
      toast.success(data.message || 'Registration successful!');
      return data;
    } catch (err) {
      const errors = err.response?.data;
      if (typeof errors === 'object') {
        const msg = Object.values(errors).flat().join(', ');
        toast.error(msg);
      } else {
        toast.error('Registration failed');
      }
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } catch {
      // ignore logout errors
    }
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
    toast.success('Logged out');
  };

  const refreshProfile = useCallback(async () => {
    if (!token) return;
    try {
      const { data } = await profileApi.get();
      const userData = {
        ...user,
        ...data,
        firstname: data.firstname || data.user?.firstname,
        lastname: data.lastname || data.user?.lastname,
        email: data.email || data.user?.email,
      };
      localStorage.setItem('user', JSON.stringify(userData));
      setUser(userData);
    } catch {
      // profile fetch failed silently
    }
  }, [token]);

  useEffect(() => {
    if (token) {
      refreshProfile();
    }
  }, [token]);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        isAuthenticated,
        login,
        register,
        logout,
        refreshProfile,
        setUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
