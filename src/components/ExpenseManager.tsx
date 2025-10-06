import { useState, useEffect } from 'react';
import { Plus, Upload, Trash2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { storage } from '../utils/storage';
import { Expense, Category } from '../types';
import { categorizeExpense } from '../utils/categories';
import { parseCSV } from '../utils/csvParser';

export default function ExpenseManager() {
  const { user } = useAuth();
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [showManualForm, setShowManualForm] = useState(false);
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    loadData();
  }, [user]);

  const loadData = () => {
    const allExpenses = storage.getExpenses().filter(e => e.userId === user?.id);
    const allCategories = storage.getCategories();
    setExpenses(allExpenses);
    setCategories(allCategories);
  };

  const handleManualSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!amount || !description || !user) return;

    const categoryId = categorizeExpense(description, categories);

    const newExpense: Expense = {
      id: `exp-${Date.now()}`,
      userId: user.id,
      categoryId,
      amount: parseFloat(amount),
      description,
      transactionDate: date,
      source: 'manual',
      createdAt: new Date().toISOString(),
    };

    const allExpenses = storage.getExpenses();
    allExpenses.push(newExpense);
    storage.setExpenses(allExpenses);

    setAmount('');
    setDescription('');
    setDate(new Date().toISOString().split('T')[0]);
    setShowManualForm(false);
    loadData();
  };

  // Uploads CSV file to backend for classification
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !user) return;

    setUploading(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      // Change URL if backend runs on a different port
      const response = await fetch('http://localhost:8000/classify-expenses/', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Backend error');
      const classifiedExpenses = await response.json();

      // Map backend response to Expense objects
      const newExpenses: Expense[] = classifiedExpenses.map((exp: any) => ({
        id: `exp-${Date.now()}-${Math.random()}`,
        userId: user.id,
        categoryId: exp.categoryId || categorizeExpense(exp.description, categories),
        amount: exp.amount,
        description: exp.description,
        transactionDate: exp.transactionDate || exp.date,
        source: 'csv_upload_backend',
        createdAt: new Date().toISOString(),
      }));

      const allExpenses = storage.getExpenses();
      allExpenses.push(...newExpenses);
      storage.setExpenses(allExpenses);

      loadData();
      alert(`Successfully imported ${newExpenses.length} classified transactions!`);
    } catch (err) {
      alert('Failed to classify and import transactions.');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleDelete = (id: string) => {
    const allExpenses = storage.getExpenses().filter(e => e.id !== id);
    storage.setExpenses(allExpenses);
    loadData();
  };

  const getCategoryName = (categoryId: string) => {
    return categories.find(c => c.id === categoryId)?.name || 'Unknown';
  };

  const getCategoryColor = (categoryId: string) => {
    return categories.find(c => c.id === categoryId)?.color || '#64748b';
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-800">Manage Expenses</h2>
        <div className="flex gap-3">
          <label className="cursor-pointer">
            <input
              type="file"
              accept=".csv"
              onChange={handleFileUpload}
              className="hidden"
              disabled={uploading}
            />
            <div className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors">
              <Upload className="w-5 h-5" />
              {uploading ? 'Uploading...' : 'Upload CSV'}
            </div>
          </label>
          <button
            onClick={() => setShowManualForm(!showManualForm)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-5 h-5" />
            Add Expense
          </button>
        </div>
      </div>

      {showManualForm && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Add New Expense</h3>
          <form onSubmit={handleManualSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Amount (₹)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-transparent"
                  placeholder="0.00"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Date
                </label>
                <input
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-transparent"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <input
                  type="text"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-transparent"
                  placeholder="e.g., Swiggy order"
                  required
                />
              </div>
            </div>
            <div className="flex gap-3">
              <button
                type="submit"
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Add Expense
              </button>
              <button
                type="button"
                onClick={() => setShowManualForm(false)}
                className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Recent Expenses</h3>
        {expenses.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            <p>No expenses recorded yet.</p>
            <p className="text-sm mt-2">Add your first expense or upload a CSV file to get started.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Date</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Description</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Category</th>
                  <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">Amount</th>
                  <th className="text-center py-3 px-4 text-sm font-semibold text-gray-700">Actions</th>
                </tr>
              </thead>
              <tbody>
                {expenses
                  .sort((a, b) => new Date(b.transactionDate).getTime() - new Date(a.transactionDate).getTime())
                  .map((expense) => (
                    <tr key={expense.id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4 text-sm text-gray-600">
                        {new Date(expense.transactionDate).toLocaleDateString()}
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-800">{expense.description}</td>
                      <td className="py-3 px-4">
                        <span
                          className="inline-block px-3 py-1 rounded-full text-xs font-medium text-white"
                          style={{ backgroundColor: getCategoryColor(expense.categoryId) }}
                        >
                          {getCategoryName(expense.categoryId)}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-sm font-semibold text-gray-800 text-right">
                        ₹{expense.amount.toFixed(2)}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <button
                          onClick={() => handleDelete(expense.id)}
                          className="text-red-600 hover:text-red-700 transition-colors"
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

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-semibold text-blue-900 mb-2">CSV Upload Format</h4>
        <p className="text-sm text-blue-800 mb-2">
          Your CSV file should contain columns for: Date, Description, and Amount
        </p>
        <p className="text-xs text-blue-700">
          Example: date,description,amount<br />
          2024-01-15,Swiggy Order,450<br />
          2024-01-16,Uber Ride,250
        </p>
      </div>
    </div>
  );
}
