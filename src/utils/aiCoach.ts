import { Expense, Category, AIAdvice, SavingsGoal } from '../types';

export function generateAdvice(
  expenses: Expense[],
  categories: Category[],
  goal: SavingsGoal | null
): AIAdvice[] {
  const advice: AIAdvice[] = [];

  const currentMonth = new Date().toISOString().slice(0, 7);
  const monthExpenses = expenses.filter(e => e.transactionDate.startsWith(currentMonth));

  if (monthExpenses.length === 0) return advice;

  const categoryTotals = new Map<string, number>();
  monthExpenses.forEach(exp => {
    const current = categoryTotals.get(exp.categoryId) || 0;
    categoryTotals.set(exp.categoryId, current + exp.amount);
  });

  const totalSpent = Array.from(categoryTotals.values()).reduce((sum, val) => sum + val, 0);

  categoryTotals.forEach((amount, categoryId) => {
    const category = categories.find(c => c.id === categoryId);
    if (!category || category.name === 'Others') return;

    const percentage = (amount / totalSpent) * 100;

    if (category.name === 'Food' && percentage > 30) {
      advice.push({
        id: `advice-food-${Date.now()}`,
        title: 'High Food Spending Detected',
        message: `You spent ${percentage.toFixed(0)}% of your budget on Food (₹${amount.toFixed(0)}). Cutting weekly food deliveries in half could save you ₹${(amount * 0.3).toFixed(0)}/month.`,
        potentialSavings: amount * 0.3,
        category: 'Food',
      });
    }

    if (category.name === 'Subscriptions' && amount > 1500) {
      advice.push({
        id: `advice-subs-${Date.now()}`,
        title: 'Subscription Review Needed',
        message: `Your subscriptions cost ₹${amount.toFixed(0)}/month. Cancelling 2 unused subscriptions could save ₹${Math.min(600, amount * 0.4).toFixed(0)}/month.`,
        potentialSavings: Math.min(600, amount * 0.4),
        category: 'Subscriptions',
      });
    }

    if (category.name === 'Shopping' && percentage > 25) {
      advice.push({
        id: `advice-shop-${Date.now()}`,
        title: 'Shopping Alert',
        message: `Shopping represents ${percentage.toFixed(0)}% of expenses. Consider setting a monthly shopping budget to save ₹${(amount * 0.25).toFixed(0)}.`,
        potentialSavings: amount * 0.25,
        category: 'Shopping',
      });
    }
  });

  if (goal && goal.active) {
    const remainingSavings = goal.monthlyTarget - totalSpent;
    if (remainingSavings < 0) {
      advice.push({
        id: `advice-goal-${Date.now()}`,
        title: 'Savings Goal at Risk',
        message: `You've exceeded your budget by ₹${Math.abs(remainingSavings).toFixed(0)}. Consider reducing discretionary spending to get back on track.`,
        category: 'Goal',
      });
    }
  }

  return advice;
}

export function detectAnomalies(expenses: Expense[], categories: Category[]): string[] {
  const alerts: string[] = [];

  const currentWeek = getWeekNumber(new Date());
  const lastWeek = currentWeek - 1;

  const thisWeekExpenses = expenses.filter(e => {
    const expDate = new Date(e.transactionDate);
    return getWeekNumber(expDate) === currentWeek;
  });

  const lastWeekExpenses = expenses.filter(e => {
    const expDate = new Date(e.transactionDate);
    return getWeekNumber(expDate) === lastWeek;
  });

  categories.forEach(category => {
    if (category.name === 'Others') return;

    const thisWeekTotal = thisWeekExpenses
      .filter(e => e.categoryId === category.id)
      .reduce((sum, e) => sum + e.amount, 0);

    const lastWeekTotal = lastWeekExpenses
      .filter(e => e.categoryId === category.id)
      .reduce((sum, e) => sum + e.amount, 0);

    if (lastWeekTotal > 0 && thisWeekTotal > lastWeekTotal * 2) {
      alerts.push(
        `This week you spent ₹${thisWeekTotal.toFixed(0)} on ${category.name} vs usual ₹${lastWeekTotal.toFixed(0)}`
      );
    }
  });

  return alerts;
}

function getWeekNumber(date: Date): number {
  const firstDayOfYear = new Date(date.getFullYear(), 0, 1);
  const pastDaysOfYear = (date.getTime() - firstDayOfYear.getTime()) / 86400000;
  return Math.ceil((pastDaysOfYear + firstDayOfYear.getDay() + 1) / 7);
}

export function generateChatResponse(
  message: string,
  expenses: Expense[],
  categories: Category[],
  goal: SavingsGoal | null
): string {
  const lowerMessage = message.toLowerCase();

  if (lowerMessage.includes('biggest') && lowerMessage.includes('expense')) {
    const currentMonth = new Date().toISOString().slice(0, 7);
    const monthExpenses = expenses.filter(e => e.transactionDate.startsWith(currentMonth));

    const categoryTotals = new Map<string, number>();
    monthExpenses.forEach(exp => {
      const current = categoryTotals.get(exp.categoryId) || 0;
      categoryTotals.set(exp.categoryId, current + exp.amount);
    });

    let maxAmount = 0;
    let maxCategory = '';

    categoryTotals.forEach((amount, categoryId) => {
      if (amount > maxAmount) {
        maxAmount = amount;
        const cat = categories.find(c => c.id === categoryId);
        maxCategory = cat?.name || 'Unknown';
      }
    });

    if (maxCategory) {
      return `Your biggest expense this month is ${maxCategory}, totaling ₹${maxAmount.toFixed(0)}. That's a significant portion of your budget!`;
    }

    return "You don't have any expenses recorded yet this month.";
  }

  if (lowerMessage.includes('save') || lowerMessage.includes('saving')) {
    const advice = generateAdvice(expenses, categories, goal);
    if (advice.length > 0) {
      const tips = advice.slice(0, 2).map(a => a.message).join(' ');
      return `Here are some savings tips: ${tips}`;
    }
    return "Great spending habits! Keep tracking your expenses to find more savings opportunities.";
  }

  if (lowerMessage.includes('goal')) {
    if (!goal || !goal.active) {
      return "You haven't set a savings goal yet. Would you like to set one to track your progress?";
    }

    const currentMonth = new Date().toISOString().slice(0, 7);
    const monthExpenses = expenses.filter(e => e.transactionDate.startsWith(currentMonth));
    const totalSpent = monthExpenses.reduce((sum, e) => sum + e.amount, 0);

    const remaining = goal.monthlyTarget - totalSpent;

    if (remaining > 0) {
      return `You're on track! You have ₹${remaining.toFixed(0)} left to stay within your ₹${goal.monthlyTarget} monthly goal. Keep it up!`;
    } else {
      return `You've exceeded your goal by ₹${Math.abs(remaining).toFixed(0)}. Don't worry, tomorrow is a fresh start!`;
    }
  }

  if (lowerMessage.includes('transport') || lowerMessage.includes('travel')) {
    const travelCat = categories.find(c => c.name === 'Travel');
    if (travelCat) {
      const currentMonth = new Date().toISOString().slice(0, 7);
      const travelExpenses = expenses.filter(
        e => e.categoryId === travelCat.id && e.transactionDate.startsWith(currentMonth)
      );
      const total = travelExpenses.reduce((sum, e) => sum + e.amount, 0);

      if (total > 0) {
        return `You've spent ₹${total.toFixed(0)} on travel this month. Consider carpooling, using public transport, or combining trips to save on fuel and fares.`;
      }
      return "You haven't recorded any travel expenses this month.";
    }
  }

  return "I'm here to help you manage your finances! Ask me about your biggest expenses, savings tips, or your progress toward your goal.";
}
