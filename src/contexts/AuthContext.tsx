import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User } from '../types';
import * as api from '../utils/api';

interface AuthContextType {
  user: User | null;
  login: (username: string, password: string) => Promise<boolean>;
  signup: (username: string, password: string, fullName: string) => Promise<boolean>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const savedUser = localStorage.getItem('fincoach_user');
    if (savedUser) {
      setUser(JSON.parse(savedUser));
    }
    setIsLoading(false);
  }, []);

  const signup = async (username: string, password: string, fullName: string): Promise<boolean> => {
    try {
      const response = await api.signup(username, password, fullName);
      if (response.success && response.user) {
        const newUser: User = {
          id: response.user.id,
          username: response.user.username,
          fullName: response.user.full_name,
          passwordHash: ''
        };
        setUser(newUser);
        localStorage.setItem('fincoach_user', JSON.stringify(newUser));
        return true;
      }
      return false;
    } catch (error) {
      console.error('Signup error:', error);
      alert('Signup failed: ' + (error as Error).message);
      return false;
    }
  };

  const login = async (username: string, password: string): Promise<boolean> => {
    try {
      const response = await api.login(username, password);
      if (response.success && response.user) {
        const loggedInUser: User = {
          id: response.user.id,
          username: response.user.username,
          fullName: response.user.full_name,
          passwordHash: ''
        };
        setUser(loggedInUser);
        localStorage.setItem('fincoach_user', JSON.stringify(loggedInUser));
        return true;
      }
      return false;
    } catch (error) {
      console.error('Login error:', error);
      alert('Login failed: ' + (error as Error).message);
      return false;
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('fincoach_user');
  };

  return (
    <AuthContext.Provider value={{ user, login, signup, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
