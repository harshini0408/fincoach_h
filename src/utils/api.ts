// src/utils/api.ts
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Authentication
export async function signup(username: string, password: string, fullName: string) {
  const response = await fetch(`${API_BASE_URL}/api/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password, full_name: fullName })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Signup failed');
  }
  
  return await response.json();
}

export async function login(username: string, password: string) {
  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Login failed');
  }
  
  return await response.json();
}

// Expenses
export async function getExpenses(userId: string) {
  const response = await fetch(`${API_BASE_URL}/api/expenses/${userId}`);
  const data = await response.json();
  return data.expenses || [];
}

export async function addExpense(userId: string, expense: any) {
  const response = await fetch(`${API_BASE_URL}/api/expenses/${userId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(expense)
  });
  
  if (!response.ok) throw new Error('Failed to add expense');
  return await response.json();
}

export async function uploadExpensesCSV(userId: string, file: File) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(`${API_BASE_URL}/api/expenses/${userId}/upload`, {
    method: 'POST',
    body: formData
  });
  
  if (!response.ok) throw new Error('Failed to upload expenses');
  return await response.json();
}

export async function deleteExpense(expenseId: string) {
  const response = await fetch(`${API_BASE_URL}/api/expenses/${expenseId}`, {
    method: 'DELETE'
  });
  
  if (!response.ok) throw new Error('Failed to delete expense');
  return await response.json();
}

// Categories
export async function getCategories() {
  const response = await fetch(`${API_BASE_URL}/api/categories`);
  const data = await response.json();
  return data.categories || [];
}

// Goals
export async function getGoals(userId: string) {
  const response = await fetch(`${API_BASE_URL}/api/goals/${userId}`);
  const data = await response.json();
  return data.goals || [];
}

export async function createGoal(userId: string, goal: any) {
  const response = await fetch(`${API_BASE_URL}/api/goals/${userId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(goal)
  });
  
  if (!response.ok) throw new Error('Failed to create goal');
  return await response.json();
}

// Chatbot
export async function sendChatMessage(userId: string, message: string, context: any = {}) {
  const response = await fetch(`${API_BASE_URL}/api/chatbot/${userId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, context })
  });
  
  if (!response.ok) throw new Error('Failed to send message');
  const data = await response.json();
  return data.response;
}
