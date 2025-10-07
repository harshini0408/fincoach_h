// src/types.ts
export interface User {
  id: string;
  username: string;
  fullName: string;
  passwordHash: string;
}

export interface Expense {
  id: string;
  userId: string;
  transactionDate: string;
  description: string;
  amount: number;
  categoryId: string;
  predicted_category?: string;  // ✅ Added this
  confidence?: number;
}

export interface Category {
  id: string;
  name: string;
  icon: string;
  color: string;
}

export interface SavingsGoal {
  id: string;
  userId: string;
  name: string;
  monthlyTarget: number;
  currentAmount: number;
  deadline?: string;
  active: boolean;
}

export interface ChatMessage {
  id: string;
  userId: string;
  message: string;
  response: string;
  createdAt: string;
}

export interface AIAdvice {
  id: string;
  message: string;
  type: 'warning' | 'success' | 'info';  // ✅ Fixed this
}
