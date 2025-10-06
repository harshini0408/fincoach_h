export interface User {
  id: string;
  username: string;
  fullName: string;
  passwordHash: string;
}

export interface Category {
  id: string;
  name: string;
  color: string;
  icon: string;
  keywords: string[];
}

export interface Expense {
  id: string;
  userId: string;
  categoryId: string;
  amount: number;
  description: string;
  transactionDate: string;
  source: 'manual' | 'csv_upload';
  createdAt: string;
}

export interface SavingsGoal {
  id: string;
  userId: string;
  monthlyTarget: number;
  currentMonth: string;
  active: boolean;
}

export interface ChatMessage {
  id: string;
  userId: string;
  message: string;
  response: string;
  createdAt: string;
}

export interface SpendingInsight {
  category: string;
  amount: number;
  percentage: number;
  color: string;
}

export interface AIAdvice {
  id: string;
  title: string;
  message: string;
  potentialSavings?: number;
  category?: string;
}
