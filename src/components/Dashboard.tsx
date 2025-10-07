import { useState, useEffect } from 'react';
import { TrendingUp, AlertCircle, CheckCircle, Info } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import * as api from '../utils/api';
import type { Expense, AIAdvice } from '../types';

export default function Dashboard() {
  const { user } = useAuth();
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [loading, setLoading] = useState(true);
  const [insights, setInsights] = useState<AIAdvice[]>([]);

  useEffect(() => {
    loadDashboardData();
  }, [user]);

  const loadDashboardData = async () => {
    if (!user) return;
    
    setLoading(true);
    try {
      const expensesData = await api.getExpenses(user.id);
      setExpenses(expensesData);
      generateInsights(expensesData);
    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateInsights = (expensesData: Expense[]) => {
    const newInsights: AIAdvice[] = [];
    const total = expensesData.reduce((sum, e) => sum + e.amount, 0);
    
    if (total > 10000) {
      newInsights.push({
        id: '1',
        message: `You've spent ₹${total.toFixed(0)} this month. Consider reviewing your budget.`,
        type: 'warning'
      });
    }
    
    if (expensesData.length > 5) {
      newInsights.push({
        id: '2',
        message: `${expensesData.length} transactions recorded. Great job tracking!`,
        type: 'success'
      });
    } else if (expensesData.length === 0) {
      newInsights.push({
        id: '3',
        message: 'No expenses recorded yet. Start tracking to see insights!',
        type: 'info'
      });
    }
    
    setInsights(newInsights);
  };

  const totalSpent = expenses.reduce((sum, exp) => sum + exp.amount, 0);
  
  // Category breakdown
  const categoryTotals: { [key: string]: number } = {};
  expenses.forEach(exp => {
    const cat = exp.predicted_category || 'Others';
    categoryTotals[cat] = (categoryTotals[cat] || 0) + exp.amount;
  });
  
  const sortedCategories = Object.entries(categoryTotals)
    .map(([category, amount]) => ({
      category,
      amount,
      percentage: totalSpent > 0 ? (amount / totalSpent) * 100 : 0
    }))
    .sort((a, b) => b.amount - a.amount);

  const biggestExpense = sortedCategories[0];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600">Here's your financial overview for this month</p>
      </div>

      {/* Alerts */}
      {insights.length > 0 && (
        <div className="space-y-3">
          {insights.map((insight) => (
            <div
              key={insight.id}
              className={`p-4 rounded-lg flex items-start gap-3 ${
                insight.type === 'warning' ? 'bg-yellow-50 border border-yellow-200' :
                insight.type === 'success' ? 'bg-green-50 border border-green-200' :
                'bg-blue-50 border border-blue-200'
              }`}
            >
              {insight.type === 'warning' && <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />}
              {insight.type === 'success' && <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />}
              {insight.type === 'info' && <Info className="w-5 h-5 text-blue-600 mt-0.5" />}
              <p className="text-sm">{insight.message}</p>
            </div>
          ))}
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <p className="text-sm text-gray-600">Total Spent</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">₹{totalSpent.toFixed(0)}</p>
          <p className="text-sm text-gray-500 mt-1">This month</p>
        </div>

        <div className="card">
          <p className="text-sm text-gray-600">Top Category</p>
          {biggestExpense ? (
            <>
              <p className="text-3xl font-bold text-gray-900 mt-2">{biggestExpense.category}</p>
              <p className="text-sm text-gray-500 mt-1">
                ₹{biggestExpense.amount.toFixed(0)} ({biggestExpense.percentage.toFixed(0)}% of total)
              </p>
            </>
          ) : (
            <p className="text-sm text-gray-500 mt-2">No expenses yet</p>
          )}
        </div>

        <div className="card">
          <p className="text-sm text-gray-600">Transactions</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">{expenses.length}</p>
          <p className="text-sm text-gray-500 mt-1">This month</p>
        </div>
      </div>

      {/* Category Breakdown */}
      {sortedCategories.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Spending by Category</h2>
          <div className="space-y-3">
            {sortedCategories.map(({ category, amount, percentage }) => (
              <div key={category}>
                <div className="flex justify-between text-sm mb-1">
                  <span>{category}</span>
                  <span className="font-semibold">₹{amount.toFixed(0)}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all"
                    style={{ width: `${percentage}%` }}
                  ></div>
                </div>
                <p className="text-xs text-gray-500 mt-1">{percentage.toFixed(1)}%</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Transactions */}
      {expenses.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Recent Transactions</h2>
          <div className="space-y-3">
            {expenses.slice(0, 5).map((expense) => (
              <div key={expense.id} className="flex justify-between items-center py-2 border-b last:border-b-0">
                <div>
                  <p className="font-medium">{expense.description}</p>
                  <p className="text-sm text-gray-500">
                    {expense.predicted_category || 'Uncategorized'} • {new Date(expense.transactionDate).toLocaleDateString()}
                  </p>
                </div>
                <p className="font-bold text-gray-900">₹{expense.amount.toFixed(2)}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
