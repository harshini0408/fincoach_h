import { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { storage } from './utils/storage';
import { DEFAULT_CATEGORIES } from './utils/categories';
import AuthForm from './components/AuthForm';
import Layout from './components/Layout';
import Dashboard from './components/Dashboard';
import ExpenseManager from './components/ExpenseManager';
import GoalsTracker from './components/GoalsTracker';
import Chatbot from './components/Chatbot';

function AppContent() {
  const { user } = useAuth();
  const [currentTab, setCurrentTab] = useState('dashboard');

  useEffect(() => {
    const categories = storage.getCategories();
    if (categories.length === 0) {
      storage.setCategories(DEFAULT_CATEGORIES);
    }
  }, []);

  if (!user) {
    return <AuthForm />;
  }

  return (
    <Layout currentTab={currentTab} onTabChange={setCurrentTab}>
      {currentTab === 'dashboard' && <Dashboard />}
      {currentTab === 'expenses' && <ExpenseManager />}
      {currentTab === 'goals' && <GoalsTracker />}
      {currentTab === 'chatbot' && <Chatbot />}
    </Layout>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
