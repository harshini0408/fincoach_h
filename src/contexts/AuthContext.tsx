import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User } from '../types';
import { storage } from '../utils/storage';

interface AuthContextType {
  user: User | null;
  login: (username: string, password: string) => Promise<boolean>;
  signup: (username: string, password: string, fullName: string) => Promise<boolean>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const currentUser = storage.getCurrentUser();
    if (currentUser) {
      setUser(currentUser);
    }
  }, []);

  const hashPassword = (password: string): string => {
    let hash = 0;
    for (let i = 0; i < password.length; i++) {
      const char = password.charCodeAt(i);
      hash = (hash << 5) - hash + char;
      hash = hash & hash;
    }
    return hash.toString();
  };

  const signup = async (username: string, password: string, fullName: string): Promise<boolean> => {
    const users = storage.getUsers();

    if (users.find(u => u.username === username)) {
      return false;
    }

    const newUser: User = {
      id: `user-${Date.now()}`,
      username,
      passwordHash: hashPassword(password),
      fullName,
    };

    users.push(newUser);
    storage.setUsers(users);

    setUser(newUser);
    storage.setCurrentUser(newUser);

    return true;
  };

  const login = async (username: string, password: string): Promise<boolean> => {
    const users = storage.getUsers();
    const foundUser = users.find(
      u => u.username === username && u.passwordHash === hashPassword(password)
    );

    if (foundUser) {
      setUser(foundUser);
      storage.setCurrentUser(foundUser);
      return true;
    }

    return false;
  };

  const logout = () => {
    setUser(null);
    storage.setCurrentUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, signup, logout }}>
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
