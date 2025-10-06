import { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { TrendingUp, AlertCircle } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { storage } from '../utils/storage';
import { Expense, Category, SpendingInsight } from '../types';
import { generateAdvice, detectAnomalies } from '../utils/aiCoach';

export default function Dashboard() {
  const { user } = useAuth();
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [insights, setInsights] = useState<SpendingInsight[]>([]);
  const [weeklyData, setWeeklyData] = useState<any[]>([]);

  useEffect(() => {
    loadData();
  }, [user]);

  const loadData = () => {
    const allExpenses = storage.getExpenses().filter(e => e.userId === user?.id);
    const allCategories = storage.getCategories();
    setExpenses(allExpenses);
    setCategories(allCategories);

    const currentMonth = new Date().toISOString().slice(0, 7);
    const monthExpenses = allExpenses.filter(e => e.transactionDate.startsWith(currentMonth));

    const categoryTotals = new Map<string, number>();
    monthExpenses.forEach(exp => {
      const current = categoryTotals.get(exp.categoryId) || 0;
      categoryTotals.set(exp.categoryId, current + exp.amount);
    });

    const totalSpent = Array.from(categoryTotals.values()).reduce((sum, val) => sum + val, 0);

    const insightsData: SpendingInsight[] = [];
    categoryTotals.forEach((amount, categoryId) => {
      const category = allCategories.find(c => c.id === categoryId);
      if (category) {
        insightsData.push({
          category: category.name,
          amount,
          percentage: (amount / totalSpent) * 100,
          color: category.color,
        });
      }
    });

    insightsData.sort((a, b) => b.amount - a.amount);
    setInsights(insightsData);

    const last4Weeks = [];
    for (let i = 3; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - (i * 7));
      const weekStart = new Date(date);
      weekStart.setDate(weekStart.getDate() - weekStart.getDay());

      const weekExpenses = allExpenses.filter(e => {
        const expDate = new Date(e.transactionDate);
        const diff = Math.abs(expDate.getTime() - weekStart.getTime());
        const diffDays = Math.ceil(diff / (1000 * 3600 * 24));
        return diffDays < 7;
      });

      const weekTotal = weekExpenses.reduce((sum, e) => sum + e.amount, 0);

      last4Weeks.push({
        week: `Week ${4 - i}`,
        amount: weekTotal,
      });
    }

    setWeeklyData(last4Weeks);
  };

  const goal = storage.getGoals().find(g => g.userId === user?.id && g.active);
  const currentMonth = new Date().toISOString().slice(0, 7);
  const monthExpenses = expenses.filter(e => e.transactionDate.startsWith(currentMonth));
  const totalSpent = monthExpenses.reduce((sum, e) => sum + e.amount, 0);

  const advice = generateAdvice(expenses, categories, goal || null);
  const anomalies = detectAnomalies(expenses, categories);

  const biggestExpense = insights.length > 0 ? insights[0] : null;

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-xl p-6 text-white">
        <h2 className="text-2xl font-bold mb-2">Welcome back, {user?.fullName}!</h2>
        <p className="text-blue-100">Here's your financial overview for this month</p>
      </div>

      {anomalies.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <h3 className="font-semibold text-yellow-900 mb-1">Spending Alerts</h3>
              {anomalies.map((alert, idx) => (
                <p key={idx} className="text-sm text-yellow-800">{alert}</p>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-600">Total Spent</h3>
            <TrendingUp className="w-5 h-5 text-blue-600" />
          </div>
          <p className="text-3xl font-bold text-gray-800">₹{totalSpent.toFixed(0)}</p>
          <p className="text-sm text-gray-500 mt-1">This month</p>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-600">Biggest Expense</h3>
          </div>
          {biggestExpense ? (
            <>
              <p className="text-2xl font-bold text-gray-800">{biggestExpense.category}</p>
              <p className="text-lg text-gray-600 mt-1">₹{biggestExpense.amount.toFixed(0)}</p>
              <p className="text-sm text-gray-500">{biggestExpense.percentage.toFixed(0)}% of total</p>
            </>
          ) : (
            <p className="text-gray-500">No expenses yet</p>
          )}
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-600">Categories</h3>
          </div>
          <p className="text-3xl font-bold text-gray-800">{insights.length}</p>
          <p className="text-sm text-gray-500 mt-1">Active this month</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Spending by Category</h3>
          {insights.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={insights}
                  dataKey="amount"
                  nameKey="category"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  label={(entry) => `${entry.category}: ${entry.percentage.toFixed(0)}%`}
                >
                  {insights.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: number) => `₹${value.toFixed(0)}`} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[300px] flex items-center justify-center text-gray-400">
              No spending data to display
            </div>
          )}
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Weekly Spending Trend</h3>
          {weeklyData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={weeklyData}>
                <XAxis dataKey="week" />
                <YAxis />
                <Tooltip formatter={(value: number) => `₹${value.toFixed(0)}`} />
                <Bar dataKey="amount" fill="#3b82f6" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[300px] flex items-center justify-center text-gray-400">
              No weekly data to display
            </div>
          )}
        </div>
      </div>

      {advice.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">AI Financial Advice</h3>
          <div className="space-y-3">
            {advice.map((item) => (
              <div key={item.id} className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="font-semibold text-blue-900 mb-1">{item.title}</h4>
                <p className="text-sm text-blue-800">{item.message}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
