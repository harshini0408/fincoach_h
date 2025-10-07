import { useState, useEffect } from 'react';
import { Plus, Upload, Trash2, TrendingUp } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import * as api from '../utils/api';
import type { Expense, Category } from '../types';

export default function ExpenseManager() {
  const { user } = useAuth();
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newExpense, setNewExpense] = useState({
    description: '',
    amount: 0,
    date: new Date().toISOString().split('T')[0]
  });

  // Load expenses and categories
  useEffect(() => {
    loadExpenses();
    loadCategories();
  }, [user]);

  const loadExpenses = async () => {
    if (!user) return;
    setLoading(true);
    try {
      const data = await api.getExpenses(user.id);
      setExpenses(data);
    } catch (error) {
      console.error('Error loading expenses:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadCategories = async () => {
    try {
      const data = await api.getCategories();
      setCategories(data);
    } catch (error) {
      console.error('Error loading categories:', error);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !user) return;

    setLoading(true);
    try {
      const result = await api.uploadExpensesCSV(user.id, file);
      alert(result.message || 'Expenses uploaded successfully!');
      await loadExpenses();
    } catch (error: any) {
      alert('Upload failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAddExpense = async () => {
    if (!user || !newExpense.description || newExpense.amount <= 0) {
      alert('Please fill in all fields');
      return;
    }
    
    try {
      // Don't send category_id - backend will auto-classify
      await api.addExpense(user.id, {
        transaction_date: newExpense.date + 'T00:00:00Z',
        description: newExpense.description,
        amount: newExpense.amount
      });
      
      await loadExpenses();
      setShowAddModal(false);
      setNewExpense({ 
        description: '', 
        amount: 0, 
        date: new Date().toISOString().split('T')[0] 
      });
    } catch (error) {
      alert('Failed to add expense');
    }
  };

  const handleDeleteExpense = async (id: string) => {
    if (!confirm('Delete this expense?')) return;
    
    try {
      await api.deleteExpense(id);
      await loadExpenses();
    } catch (error) {
      alert('Failed to delete expense');
    }
  };

  const getCategoryName = (categoryId: string, predictedCategory?: string) => {
    // Show predicted category if available, otherwise lookup by ID
    if (predictedCategory) {
      return `🤖 ${predictedCategory}`;
    }
    const category = categories.find(c => c.id === categoryId);
    return category ? `${category.icon} ${category.name}` : 'Unknown';
  };

  const totalSpent = expenses.reduce((sum, exp) => sum + exp.amount, 0);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Expense Manager</h1>
          <p className="text-gray-600">Track and categorize your expenses</p>
        </div>
        <div className="flex gap-3">
          <label className="btn-secondary cursor-pointer">
            <Upload className="w-5 h-5 inline mr-2" />
            Upload CSV
            <input
              type="file"
              accept=".csv"
              onChange={handleFileUpload}
              className="hidden"
            />
          </label>
          <button onClick={() => setShowAddModal(true)} className="btn-primary">
            <Plus className="w-5 h-5 inline mr-2" />
            Add Expense
          </button>
        </div>
      </div>

      {/* Summary Card */}
      <div className="card">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600">Total Expenses</p>
            <p className="text-3xl font-bold text-gray-900">₹{totalSpent.toFixed(2)}</p>
          </div>
          <div className="bg-blue-100 p-3 rounded-lg">
            <TrendingUp className="w-8 h-8 text-blue-600" />
          </div>
        </div>
        <p className="text-sm text-gray-500 mt-2">{expenses.length} transactions recorded</p>
      </div>

      {/* Expenses Table */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Recent Expenses</h2>
        
        {loading ? (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-2 text-gray-600">Loading expenses...</p>
          </div>
        ) : expenses.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500">No expenses recorded yet.</p>
            <p className="text-sm text-gray-400 mt-2">Add your first expense or upload a CSV file to get started.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4">Date</th>
                  <th className="text-left py-3 px-4">Description</th>
                  <th className="text-left py-3 px-4">Category</th>
                  <th className="text-right py-3 px-4">Amount</th>
                  <th className="text-center py-3 px-4">Actions</th>
                </tr>
              </thead>
              <tbody>
                {expenses.map((expense) => (
                  <tr key={expense.id} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-4">
                      {new Date(expense.transactionDate).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4">{expense.description}</td>
                    <td className="py-3 px-4">
                      {getCategoryName(expense.categoryId, expense.predicted_category)}
                      {expense.confidence && (
                        <span className="text-xs text-gray-500 ml-2">
                          ({(expense.confidence * 100).toFixed(0)}%)
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right font-semibold">
                      ₹{expense.amount.toFixed(2)}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <button
                        onClick={() => handleDeleteExpense(expense.id)}
                        className="text-red-600 hover:text-red-800"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add Expense Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Add New Expense</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Description</label>
                <input
                  type="text"
                  value={newExpense.description}
                  onChange={(e) => setNewExpense({...newExpense, description: e.target.value})}
                  className="w-full px-3 py-2 border rounded-lg"
                  placeholder="e.g., Grocery shopping, Uber ride, Netflix"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Amount (₹)</label>
                <input
                  type="number"
                  value={newExpense.amount}
                  onChange={(e) => setNewExpense({...newExpense, amount: parseFloat(e.target.value) || 0})}
                  className="w-full px-3 py-2 border rounded-lg"
                  placeholder="0.00"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Date</label>
                <input
                  type="date"
                  value={newExpense.date}
                  onChange={(e) => setNewExpense({...newExpense, date: e.target.value})}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>

              <div className="bg-blue-50 p-3 rounded-lg">
                <p className="text-xs text-blue-800">
                  💡 No need to select category - our AI will automatically categorize your expense!
                </p>
              </div>
            </div>
            
            <div className="flex gap-3 mt-6">
              <button onClick={() => setShowAddModal(false)} className="flex-1 btn-secondary">
                Cancel
              </button>
              <button onClick={handleAddExpense} className="flex-1 btn-primary">
                Add Expense
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
