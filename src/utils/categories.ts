import { Category } from '../types';

export const DEFAULT_CATEGORIES: Category[] = [
  {
    id: 'cat-1',
    name: 'Food',
    color: '#ef4444',
    icon: 'utensils',
    keywords: ['swiggy', 'zomato', 'food', 'restaurant', 'cafe', 'dominos', 'mcdonald', 'kfc', 'pizza', 'burger', 'dining', 'lunch', 'dinner', 'breakfast'],
  },
  {
    id: 'cat-2',
    name: 'Travel',
    color: '#3b82f6',
    icon: 'car',
    keywords: ['uber', 'ola', 'rapido', 'metro', 'petrol', 'fuel', 'bus', 'train', 'flight', 'taxi', 'transport', 'commute'],
  },
  {
    id: 'cat-3',
    name: 'Shopping',
    color: '#8b5cf6',
    icon: 'shopping-bag',
    keywords: ['amazon', 'flipkart', 'myntra', 'ajio', 'shopping', 'mall', 'retail', 'store', 'online', 'purchase'],
  },
  {
    id: 'cat-4',
    name: 'Bills',
    color: '#eab308',
    icon: 'receipt',
    keywords: ['electricity', 'water', 'gas', 'bill', 'utility', 'internet', 'broadband', 'mobile', 'recharge', 'phone'],
  },
  {
    id: 'cat-5',
    name: 'Subscriptions',
    color: '#ec4899',
    icon: 'refresh-cw',
    keywords: ['netflix', 'prime', 'spotify', 'subscription', 'membership', 'gym', 'youtube', 'disney', 'hotstar'],
  },
  {
    id: 'cat-7',
    name: 'Entertainment',
    color: '#f59e42',
    icon: 'film',
    keywords: ['movie', 'cinema', 'concert', 'cricket', 'music', 'show', 'event', 'tickets', 'night'],
  },
  {
    id: 'cat-8',
    name: 'Groceries',
    color: '#22c55e',
    icon: 'shopping-cart',
    keywords: ['grocery', 'groceries', 'vegetables', 'milk', 'bread', 'bazaar', 'instamart', 'market', 'flour', 'rice', 'dal', 'pulses', 'oil', 'eggs', 'packet', 'loaf', 'detergent'],
  },
  {
    id: 'cat-9',
    name: 'Health',
    color: '#0ea5e9',
    icon: 'heart',
    keywords: ['medicine', 'doctor', 'pharmacy', 'toothpaste', 'toothbrush', 'soap', 'shampoo', 'consultation', 'vaccination', 'medical', 'insurance'],
  },
  {
    id: 'cat-10',
    name: 'Transport',
    color: '#6366f1',
    icon: 'truck',
    keywords: ['petrol', 'car', 'bike', 'repair', 'service', 'refill', 'transport'],
  },
  {
    id: 'cat-6',
    name: 'Others',
    color: '#64748b',
    icon: 'more-horizontal',
    keywords: [],
  },
];

export function categorizeExpense(description: string, categories: Category[]): string {
  const lowerDesc = description.toLowerCase();

  for (const category of categories) {
    if (category.name === 'Others') continue;

    for (const keyword of category.keywords) {
      if (lowerDesc.includes(keyword.toLowerCase())) {
        return category.id;
      }
    }
  }

  return categories.find(c => c.name === 'Others')?.id || categories[categories.length - 1].id;
}
