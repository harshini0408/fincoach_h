# FinCoach - AI-Powered Personal Finance Assistant

A full-stack demo application that helps you manage your personal finances with AI-powered insights and recommendations.

## Features

### 1. Authentication
- Secure signup and login system
- User profile management
- Session persistence

### 2. Expense Management
- **Manual Entry**: Add expenses one at a time with automatic categorization
- **CSV Upload**: Import bank statements in bulk (see sample-transactions.csv)
- **Smart Categorization**: AI-powered keyword matching automatically categorizes expenses into:
  - Food (Swiggy, Zomato, restaurants)
  - Travel (Uber, Ola, petrol, metro)
  - Shopping (Amazon, Flipkart, Myntra)
  - Bills (electricity, water, internet)
  - Subscriptions (Netflix, Spotify, gym)
  - Others (miscellaneous)

### 3. Interactive Dashboard
- **Visual Charts**: Pie chart showing spending breakdown by category
- **Trend Analysis**: Bar chart displaying weekly spending patterns
- **Key Metrics**: Total spent, biggest expense category, active categories
- **Anomaly Detection**: Alerts for unusual spending patterns

### 4. AI Financial Coach
- **Smart Insights**: Get personalized advice based on your spending patterns
- **Actionable Tips**: Specific recommendations with potential savings amounts
- **Budget Alerts**: Warnings when spending exceeds typical patterns
- **Category Analysis**: Detailed breakdown of spending in each category

### 5. Savings Goal Tracker
- Set monthly budget targets
- Real-time progress tracking with visual progress bar
- On-track vs over-budget status indicators
- Remaining budget calculations

### 6. AI Chatbot
- Interactive chat interface for financial questions
- Ask about:
  - "What's my biggest expense this month?"
  - "How can I save on transport?"
  - "Am I close to my goal?"
  - "Give me savings tips"
- Context-aware responses based on your actual spending data

### 7. Additional Features
- **Dark Mode**: Toggle between light and dark themes
- **Responsive Design**: Works seamlessly on mobile, tablet, and desktop
- **Data Persistence**: All data stored locally in browser

## Getting Started

### Quick Start
1. Sign up with a username, password, and full name
2. Set your monthly budget goal
3. Add expenses manually or upload the sample CSV file
4. Explore the dashboard to see your spending visualized
5. Chat with the AI coach for personalized advice

### Demo CSV Upload
Use the included `sample-transactions.csv` file to test the bulk import feature:
- Contains 20 sample transactions across all categories
- Demonstrates automatic categorization
- Shows realistic spending patterns

### CSV Format
Your CSV file should have these columns:
```
date,description,amount
2024-10-01,Swiggy Order,450
2024-10-02,Uber Ride,180
```

## Tech Stack

- **Frontend**: React + TypeScript
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **Icons**: Lucide React
- **Storage**: LocalStorage
- **Build Tool**: Vite

## AI Features

### Expense Categorization
Uses keyword-based machine learning to automatically categorize transactions:
- Matches transaction descriptions against category keywords
- Learns from common spending patterns
- Falls back to "Others" for unknown categories

### Financial Advice Generation
Analyzes spending patterns to generate personalized advice:
- Identifies high-spending categories (>30% of budget)
- Detects unused subscriptions
- Calculates potential savings
- Provides actionable recommendations

### Anomaly Detection
Compares weekly spending to identify unusual patterns:
- Flags spending that's 2x normal levels
- Highlights categories with sudden increases
- Helps catch budget leaks early

### Chatbot Intelligence
Context-aware responses using your actual data:
- Queries your expense history
- References your savings goals
- Provides category-specific advice
- Offers conversational financial guidance

## Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Type check
npm run typecheck
```

## Project Structure

```
src/
├── components/         # React components
│   ├── AuthForm.tsx    # Login/signup
│   ├── Dashboard.tsx   # Main dashboard with charts
│   ├── ExpenseManager.tsx  # Add/upload expenses
│   ├── GoalsTracker.tsx    # Savings goals
│   ├── Chatbot.tsx     # AI chat interface
│   └── Layout.tsx      # App layout with navigation
├── contexts/           # React contexts
│   └── AuthContext.tsx # Authentication state
├── utils/              # Utility functions
│   ├── storage.ts      # LocalStorage helpers
│   ├── categories.ts   # Category definitions & ML
│   ├── csvParser.ts    # CSV parsing logic
│   └── aiCoach.ts      # AI advice & chat logic
├── types.ts            # TypeScript types
├── App.tsx             # Main app component
└── main.tsx            # App entry point
```

## Future Enhancements

- Backend API integration with FastAPI
- Real ML model for categorization (scikit-learn)
- Integration with actual LLM for chatbot
- PDF report generation
- Gamification with badges and streaks
- Budget forecasting
- Expense reminders
- Multi-currency support
- Receipt photo upload with OCR

## Notes

- All data is stored in browser localStorage
- No backend server required for demo
- Clear browser data to reset the application
- Works offline after initial load
