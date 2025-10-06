import { useState, useEffect } from 'react';
import { Target, TrendingUp, TrendingDown } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { storage } from '../utils/storage';
import { SavingsGoal, Expense } from '../types';

export default function GoalsTracker() {
  const { user } = useAuth();
  const [goal, setGoal] = useState<SavingsGoal | null>(null);
  const [monthlyTarget, setMonthlyTarget] = useState('');
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    loadData();
  }, [user]);

  const loadData = () => {
    const allGoals = storage.getGoals().filter(g => g.userId === user?.id);
    const activeGoal = allGoals.find(g => g.active);
    setGoal(activeGoal || null);

    const allExpenses = storage.getExpenses().filter(e => e.userId === user?.id);
    setExpenses(allExpenses);

    if (!activeGoal) {
      setShowForm(true);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!monthlyTarget || !user) return;

    const currentMonth = new Date().toISOString().slice(0, 7);

    const allGoals = storage.getGoals();
    allGoals.forEach(g => {
      if (g.userId === user.id) {
        g.active = false;
      }
    });

    const newGoal: SavingsGoal = {
      id: `goal-${Date.now()}`,
      userId: user.id,
      monthlyTarget: parseFloat(monthlyTarget),
      currentMonth,
      active: true,
    };

    allGoals.push(newGoal);
    storage.setGoals(allGoals);

    setMonthlyTarget('');
    setShowForm(false);
    loadData();
  };

  const currentMonth = new Date().toISOString().slice(0, 7);
  const monthExpenses = expenses.filter(e => e.transactionDate.startsWith(currentMonth));
  const totalSpent = monthExpenses.reduce((sum, e) => sum + e.amount, 0);

  const remaining = goal ? goal.monthlyTarget - totalSpent : 0;
  const progress = goal ? Math.min((totalSpent / goal.monthlyTarget) * 100, 100) : 0;
  const isOnTrack = remaining >= 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-800">Savings Goals</h2>
        {goal && (
          <button
            onClick={() => setShowForm(!showForm)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Update Goal
          </button>
        )}
      </div>

      {showForm && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">
            {goal ? 'Update Monthly Goal' : 'Set Monthly Savings Goal'}
          </h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Monthly Budget Target (₹)
              </label>
              <input
                type="number"
                step="0.01"
                value={monthlyTarget}
                onChange={(e) => setMonthlyTarget(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-transparent"
                placeholder="e.g., 50000"
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                Set a monthly spending limit to track your savings
              </p>
            </div>
            <div className="flex gap-3">
              <button
                type="submit"
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                {goal ? 'Update Goal' : 'Set Goal'}
              </button>
              {goal && (
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                >
                  Cancel
                </button>
              )}
            </div>
          </form>
        </div>
      )}

      {goal && (
        <>
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="bg-blue-100 rounded-full p-3">
                <Target className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-800">Monthly Budget Goal</h3>
                <p className="text-sm text-gray-600">
                  {new Date().toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
                </p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-600">Progress</span>
                  <span className="text-sm font-semibold text-gray-800">
                    {progress.toFixed(0)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-4">
                  <div
                    className={`h-4 rounded-full transition-all ${
                      isOnTrack ? 'bg-green-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4">
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-sm text-gray-600 mb-1">Budget Target</p>
                  <p className="text-2xl font-bold text-gray-800">₹{goal.monthlyTarget.toFixed(0)}</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-sm text-gray-600 mb-1">Total Spent</p>
                  <p className="text-2xl font-bold text-gray-800">₹{totalSpent.toFixed(0)}</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-sm text-gray-600 mb-1">
                    {isOnTrack ? 'Remaining' : 'Over Budget'}
                  </p>
                  <p className={`text-2xl font-bold ${isOnTrack ? 'text-green-600' : 'text-red-600'}`}>
                    ₹{Math.abs(remaining).toFixed(0)}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className={`rounded-lg p-6 ${
            isOnTrack
              ? 'bg-green-50 border border-green-200'
              : 'bg-red-50 border border-red-200'
          }`}>
            <div className="flex items-start gap-3">
              {isOnTrack ? (
                <TrendingUp className="w-6 h-6 text-green-600 mt-1 flex-shrink-0" />
              ) : (
                <TrendingDown className="w-6 h-6 text-red-600 mt-1 flex-shrink-0" />
              )}
              <div>
                <h4 className={`font-semibold mb-2 ${
                  isOnTrack ? 'text-green-900' : 'text-red-900'
                }`}>
                  {isOnTrack ? 'Great Job! You\'re On Track' : 'Budget Alert'}
                </h4>
                <p className={`text-sm ${
                  isOnTrack ? 'text-green-800' : 'text-red-800'
                }`}>
                  {isOnTrack
                    ? `You have ₹${remaining.toFixed(0)} remaining in your budget. Keep up the good work and stay mindful of your spending!`
                    : `You've exceeded your monthly budget by ₹${Math.abs(remaining).toFixed(0)}. Consider reviewing your expenses and adjusting your spending habits.`
                  }
                </p>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
