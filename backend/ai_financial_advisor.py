"""
FinCoach AI Financial Advisor - Simplified Version
Generates personalized financial advice without external LLM dependencies
"""

import pandas as pd
import json
from datetime import datetime
import os
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')


class FinancialAdvisor:
    """
    Intelligent Financial Advisor with rule-based advice generation
    
    Features:
    - Personalized spending advice generation
    - Budget recommendations based on 50/30/20 rule
    - Anomaly explanations in plain language
    - Goal-oriented financial planning
    - Category-specific recommendations
    """
    
    def __init__(self):
        print("✅ AI Financial Advisor initialized (Smart Fallback Mode)")
        self.is_initialized = True
        
        # Financial advice templates and rules
        self.advice_rules = {
            'high_food_spending': {
                'threshold': 30,  # % of total spending
                'advice': "Consider meal planning and cooking at home more often",
                'action': "Try the '3 home meals challenge' - cook 3 more meals at home per week"
            },
            'high_shopping_spending': {
                'threshold': 25,
                'advice': "Review your shopping habits and avoid impulse purchases",
                'action': "Use the '24-hour rule' - wait a day before buying non-essentials over ₹500"
            },
            'high_travel_spending': {
                'threshold': 25,
                'advice': "Look for cost-effective transportation options",
                'action': "Try carpooling or public transport twice a week"
            },
            'many_transactions': {
                'threshold': 150,  # number of transactions
                'advice': "You have many small transactions - consider consolidating purchases",
                'action': "Plan weekly shopping trips instead of daily purchases"
            }
        }
    
    def analyze_spending_patterns(self, classified_transactions, anomalies=None):
        """
        Analyze user spending patterns to generate insights
        
        Args:
            classified_transactions (DataFrame): Transactions with categories
            anomalies (list): Detected anomalies from anomaly detector
            
        Returns:
            dict: Spending analysis with insights
        """
        df = classified_transactions.copy()
        
        # Get category column name
        category_col = 'predicted_category' if 'predicted_category' in df.columns else 'category'
        
        analysis = {
            'total_spending': df['amount'].sum(),
            'transaction_count': len(df),
            'avg_transaction': df['amount'].mean(),
            'spending_by_category': {},
            'top_spending_categories': [],
            'spending_insights': [],
            'budget_suggestions': {},
            'financial_health_score': 0
        }
        
        # Category analysis
        category_spending = df.groupby(category_col)['amount'].agg(['sum', 'count', 'mean']).round(2)
        total_spending = df['amount'].sum()
        
        for category, row in category_spending.iterrows():
            percentage = (row['sum'] / total_spending) * 100
            analysis['spending_by_category'][category] = {
                'amount': row['sum'],
                'percentage': round(percentage, 1),
                'transactions': row['count'],
                'avg_per_transaction': row['mean']
            }
        
        # Top spending categories
        analysis['top_spending_categories'] = category_spending.sort_values('sum', ascending=False).head(3).index.tolist()
        
        # Generate insights
        insights = []
        health_score = 100  # Start with perfect score
        
        # Analyze each category
        for category, data in analysis['spending_by_category'].items():
            percentage = data['percentage']
            
            if category == 'Food' and percentage > 30:
                insights.append(f"🍽️ Food spending is {percentage}% of budget - ideal is under 25%")
                health_score -= 10
            elif category == 'Shopping' and percentage > 20:
                insights.append(f"🛍️ Shopping spending is {percentage}% - consider reducing non-essentials")
                health_score -= 8
            elif category == 'Travel' and percentage > 20:
                insights.append(f"🚗 Travel costs are {percentage}% - look for alternatives")
                health_score -= 6
            elif category in ['Bills', 'Subscriptions'] and percentage > 15:
                insights.append(f"📱 {category} spending is {percentage}% - review subscriptions")
                health_score -= 5
        
        # Transaction frequency insights
        if analysis['transaction_count'] > 200:
            insights.append(f"📊 You made {analysis['transaction_count']} transactions - very active spending!")
            health_score -= 5
        elif analysis['transaction_count'] > 100:
            insights.append(f"📊 {analysis['transaction_count']} transactions shows regular spending habits")
        
        # Average transaction insights
        if analysis['avg_transaction'] > 3000:
            insights.append(f"💳 High average transaction of ₹{analysis['avg_transaction']:.0f} - mostly big purchases")
        elif analysis['avg_transaction'] < 500:
            insights.append(f"💳 Low average transaction of ₹{analysis['avg_transaction']:.0f} - many small purchases")
        
        analysis['spending_insights'] = insights
        analysis['financial_health_score'] = max(health_score, 0)
        
        # Budget suggestions (50/30/20 rule)
        analysis['budget_suggestions'] = {
            'needs_budget': round(total_spending * 0.5, 0),  # 50% for needs
            'wants_budget': round(total_spending * 0.3, 0),  # 30% for wants
            'savings_budget': round(total_spending * 0.2, 0),  # 20% for savings
            'emergency_fund_target': round(total_spending * 6, 0)  # 6 months expenses
        }
        
        return analysis
    
    def generate_category_specific_advice(self, category, data, total_spending):
        """Generate specific advice for each spending category"""
        
        percentage = data['percentage']
        amount = data['amount']
        transactions = data['transactions']
        
        advice = {
            'category': category,
            'current_spending': amount,
            'percentage': percentage,
            'status': 'good',
            'recommendation': '',
            'action_items': [],
            'savings_potential': 0
        }
        
        if category == 'Food':
            if percentage > 30:
                advice['status'] = 'high'
                advice['recommendation'] = f"Food spending at {percentage}% is above the ideal 25%. Focus on home cooking and meal planning."
                advice['action_items'] = [
                    "Plan weekly meals and create shopping lists",
                    "Cook 3 more meals at home per week",
                    "Limit food delivery to weekends only",
                    f"Target: Reduce by ₹{amount * 0.15:.0f} (15% reduction)"
                ]
                advice['savings_potential'] = amount * 0.15
            elif percentage > 25:
                advice['status'] = 'moderate'
                advice['recommendation'] = f"Food spending at {percentage}% is slightly high but manageable."
                advice['action_items'] = ["Track food delivery expenses", "Try batch cooking on weekends"]
                advice['savings_potential'] = amount * 0.08
        
        elif category == 'Shopping':
            if percentage > 25:
                advice['status'] = 'high'
                advice['recommendation'] = f"Shopping at {percentage}% suggests frequent non-essential purchases."
                advice['action_items'] = [
                    "Use the '24-hour rule' for purchases over ₹500",
                    "Create a monthly shopping budget",
                    "Avoid impulse buying - make lists first",
                    f"Target: Save ₹{amount * 0.20:.0f} monthly"
                ]
                advice['savings_potential'] = amount * 0.20
            elif percentage > 15:
                advice['status'] = 'moderate'
                advice['recommendation'] = "Shopping spending is reasonable but can be optimized."
                advice['action_items'] = ["Compare prices before buying", "Look for deals and discounts"]
                advice['savings_potential'] = amount * 0.10
        
        elif category == 'Travel':
            if percentage > 20:
                advice['status'] = 'high'
                advice['recommendation'] = f"Travel costs at {percentage}% are quite high. Consider alternatives."
                advice['action_items'] = [
                    "Use public transport 2-3 times per week",
                    "Combine errands into single trips",
                    "Consider carpooling for regular routes",
                    f"Potential monthly savings: ₹{amount * 0.18:.0f}"
                ]
                advice['savings_potential'] = amount * 0.18
        
        elif category in ['Bills', 'Subscriptions']:
            if percentage > 15:
                advice['status'] = 'moderate'
                advice['recommendation'] = f"{category} at {percentage}% - review for unused services."
                advice['action_items'] = [
                    f"Audit all {category.lower()} monthly",
                    "Cancel unused subscriptions",
                    "Negotiate better rates where possible"
                ]
                advice['savings_potential'] = amount * 0.12
        
        else:  # Others category
            if percentage > 10:
                advice['recommendation'] = f"{category} spending needs categorization for better tracking."
                advice['action_items'] = ["Review and categorize 'Others' expenses properly"]
        
        return advice
    
    def generate_advice(self, spending_analysis, anomalies=None, user_goals=None):
        """
        Generate comprehensive personalized financial advice
        
        Args:
            spending_analysis (dict): Analyzed spending patterns
            anomalies (list): Detected spending anomalies
            user_goals (dict): User's financial goals
            
        Returns:
            str: Generated financial advice
        """
        
        total_spending = spending_analysis['total_spending']
        top_categories = spending_analysis['top_spending_categories']
        health_score = spending_analysis['financial_health_score']
        
        advice_parts = []
        advice_parts.append("## 💰 Your Personalized Financial Advice")
        advice_parts.append("")
        
        # Financial Health Score
        advice_parts.append("### 🎯 Financial Health Score")
        if health_score >= 80:
            advice_parts.append(f"**{health_score}/100** - Excellent! Your spending habits are well-balanced. 🌟")
        elif health_score >= 60:
            advice_parts.append(f"**{health_score}/100** - Good financial habits with room for improvement. 👍")
        elif health_score >= 40:
            advice_parts.append(f"**{health_score}/100** - Some concerns in your spending patterns. 📊")
        else:
            advice_parts.append(f"**{health_score}/100** - Significant room for improvement in spending habits. 🎯")
        
        advice_parts.append("")
        
        # Key Insights
        advice_parts.append("### 📊 Key Insights")
        advice_parts.append(f"You spent **₹{total_spending:.0f}** across **{spending_analysis['transaction_count']} transactions** with an average of **₹{spending_analysis['avg_transaction']:.0f}** per transaction.")
        advice_parts.append("")
        
        # Top spending breakdown
        advice_parts.append("**Your Top 3 Expense Categories:**")
        total_savings_potential = 0
        
        for i, category in enumerate(top_categories[:3], 1):
            cat_data = spending_analysis['spending_by_category'][category]
            advice_parts.append(f"{i}. **{category}**: ₹{cat_data['amount']:.0f} ({cat_data['percentage']}%) - {cat_data['transactions']} transactions")
            
            # Generate category-specific advice
            cat_advice = self.generate_category_specific_advice(category, cat_data, total_spending)
            total_savings_potential += cat_advice['savings_potential']
        
        advice_parts.append("")
        
        # Specific Recommendations
        advice_parts.append("### 🎯 Personalized Recommendations")
        
        recommendation_count = 1
        
        # Top category recommendation
        top_category = top_categories[0]
        top_data = spending_analysis['spending_by_category'][top_category]
        top_advice = self.generate_category_specific_advice(top_category, top_data, total_spending)
        
        advice_parts.append(f"**{recommendation_count}. Optimize {top_category} Spending**")
        advice_parts.append(f"   {top_advice['recommendation']}")
        if top_advice['action_items']:
            advice_parts.append("   **Action Steps:**")
            for action in top_advice['action_items'][:3]:  # Top 3 actions
                advice_parts.append(f"   • {action}")
        advice_parts.append("")
        recommendation_count += 1
        
        # Emergency Fund Recommendation
        advice_parts.append(f"**{recommendation_count}. Build Emergency Fund**")
        emergency_target = spending_analysis['budget_suggestions']['emergency_fund_target']
        monthly_emergency_savings = emergency_target / 12  # Build over 1 year
        advice_parts.append(f"   Target: **₹{emergency_target:.0f}** (6 months of expenses)")
        advice_parts.append(f"   **Action**: Save ₹{monthly_emergency_savings:.0f} monthly in a separate savings account")
        advice_parts.append("   **Why**: Protects you from unexpected financial emergencies")
        advice_parts.append("")
        recommendation_count += 1
        
        # Budget Allocation Recommendation
        advice_parts.append(f"**{recommendation_count}. Follow the 50-30-20 Budget Rule**")
        needs_budget = spending_analysis['budget_suggestions']['needs_budget']
        wants_budget = spending_analysis['budget_suggestions']['wants_budget']
        savings_budget = spending_analysis['budget_suggestions']['savings_budget']
        
        advice_parts.append("   **Ideal Monthly Allocation:**")
        advice_parts.append(f"   • **Needs** (Food, Bills, Transport): ₹{needs_budget:.0f} (50%)")
        advice_parts.append(f"   • **Wants** (Shopping, Entertainment): ₹{wants_budget:.0f} (30%)")
        advice_parts.append(f"   • **Savings & Investments**: ₹{savings_budget:.0f} (20%)")
        advice_parts.append("")
        recommendation_count += 1
        
        # Anomaly-based recommendations
        if anomalies:
            high_anomalies = [a for a in anomalies if a.get('severity') == 'high']
            if high_anomalies:
                advice_parts.append(f"**{recommendation_count}. Review Unusual Spending**")
                for anomaly in high_anomalies[:2]:  # Top 2 anomalies
                    category = anomaly.get('category', 'Unknown')
                    explanation = anomaly.get('explanation', 'Unusual spending pattern detected')
                    advice_parts.append(f"   • **{category}**: {explanation}")
                advice_parts.append("   **Action**: Review recent transactions for any errors or overspending")
                advice_parts.append("")
        
        # Monthly Challenge
        advice_parts.append("### 🏆 This Month's Challenge")
        if total_savings_potential > 0:
            advice_parts.append(f"**'Smart Saver Challenge'**: Save ₹{total_savings_potential:.0f} this month by following the recommendations above!")
        else:
            challenge_savings = total_spending * 0.10  # 10% challenge
            advice_parts.append(f"**'10% Savings Challenge'**: Reduce your total spending by 10% to save ₹{challenge_savings:.0f} this month!")
        
        advice_parts.append("")
        advice_parts.append("**Steps to Success:**")
        advice_parts.append("1. Set weekly spending check-ins every Sunday")
        advice_parts.append("2. Use FinCoach to track progress daily")
        advice_parts.append("3. Celebrate small wins - every ₹100 saved counts!")
        advice_parts.append("4. Adjust the plan if needed - progress over perfection!")
        
        advice_parts.append("")
        advice_parts.append("### 📱 Next Steps")
        advice_parts.append("✅ Set up category-wise budget alerts in FinCoach")
        advice_parts.append("✅ Review your spending weekly")
        advice_parts.append("✅ Track your savings progress")
        advice_parts.append("✅ Revisit this advice next month to see improvements")
        
        return "\n".join(advice_parts)
    
    def create_comprehensive_report(self, classified_transactions, anomaly_report=None, user_goals=None):
        """
        Create a comprehensive financial advice report
        
        Args:
            classified_transactions (DataFrame): Categorized transactions
            anomaly_report (dict): Anomaly detection results
            user_goals (dict): User financial goals
            
        Returns:
            dict: Complete financial advice report
        """
        
        print("\n📊 Generating Comprehensive Financial Report...")
        
        # Analyze spending patterns
        spending_analysis = self.analyze_spending_patterns(classified_transactions)
        
        # Extract anomalies for advice generation
        all_anomalies = []
        if anomaly_report:
            if 'statistical_anomalies' in anomaly_report and 'anomalies' in anomaly_report['statistical_anomalies']:
                all_anomalies.extend(anomaly_report['statistical_anomalies']['anomalies'])
            if 'ml_anomalies' in anomaly_report and 'anomalies' in anomaly_report['ml_anomalies']:
                all_anomalies.extend(anomaly_report['ml_anomalies']['anomalies'][:3])
        
        # Generate personalized advice
        advice = self.generate_advice(spending_analysis, all_anomalies, user_goals)
        
        # Calculate total savings potential
        total_savings_potential = 0
        for category in spending_analysis['top_spending_categories'][:3]:
            cat_data = spending_analysis['spending_by_category'][category]
            cat_advice = self.generate_category_specific_advice(category, cat_data, spending_analysis['total_spending'])
            total_savings_potential += cat_advice['savings_potential']
        
        # Compile comprehensive report
        report = {
            'report_id': f"fincoach_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'user_id': 'default_user',
            'spending_analysis': spending_analysis,
            'ai_advice': advice,
            'financial_health_score': spending_analysis['financial_health_score'],
            'anomaly_summary': {
                'total_anomalies': len(all_anomalies),
                'high_priority': len([a for a in all_anomalies if a.get('severity') == 'high']),
                'categories_affected': list(set([a.get('category') for a in all_anomalies if a.get('category')]))
            } if all_anomalies else {'total_anomalies': 0, 'high_priority': 0, 'categories_affected': []},
            'recommendations': {
                'budget_allocation': spending_analysis['budget_suggestions'],
                'total_savings_potential': round(total_savings_potential, 0),
                'top_optimization_category': spending_analysis['top_spending_categories'][0] if spending_analysis['top_spending_categories'] else None,
                'emergency_fund_target': spending_analysis['budget_suggestions']['emergency_fund_target']
            }
        }
        
        print("✅ Financial advice report generated successfully!")
        
        return report


# =====================================================================
# DEMO AND TESTING FUNCTIONS
# =====================================================================

def demo_ai_advisor():
    """Demo the AI Financial Advisor with sample data"""
    
    print("\n" + "="*70)
    print("FINCOACH AI FINANCIAL ADVISOR - DEMO")
    print("="*70)
    
    try:
        # Load sample data
        import pandas as pd
        
        # Try to load classified data or original dataset
        try:
            from expense_classifier import ExpenseClassifier
            transactions_df = pd.read_csv('expenses_dataset.csv')
            
            # Check if model exists
            import os
            if os.path.exists('expense_classifier_model.pkl'):
                print("📊 Using trained expense classifier...")
                classifier = ExpenseClassifier()
                classifier.load_model('expense_classifier_model.pkl')
                classified_df = classifier.classify_batch(transactions_df)
            else:
                print("📊 Using original dataset categories...")
                classified_df = transactions_df.copy()
                classified_df['predicted_category'] = classified_df['category']
        
        except ImportError:
            print("📊 Loading dataset directly...")
            classified_df = pd.read_csv('expenses_dataset.csv')
            classified_df['predicted_category'] = classified_df['category']
        
        # Initialize AI advisor
        advisor = FinancialAdvisor()
        
        # Try to get anomaly report
        anomaly_report = None
        try:
            from anomaly_detector import SpendingAnomalyDetector
            print("🔍 Running anomaly detection...")
            detector = SpendingAnomalyDetector()
            anomaly_report = detector.generate_anomaly_report(classified_df)
        except Exception as e:
            print(f"⚠️ Anomaly detection skipped: {str(e)}")
        
        # Generate comprehensive report
        print("\n🤖 Generating AI financial advice...")
        
        sample_goals = {
            'monthly_savings_target': '₹8000',
            'main_goal': 'Build emergency fund and optimize spending habits'
        }
        
        report = advisor.create_comprehensive_report(
            classified_df, 
            anomaly_report, 
            sample_goals
        )
        
        # Display results
        print("\n" + "="*70)
        print("📋 AI FINANCIAL ADVISOR REPORT")
        print("="*70)
        
        print(f"\n📊 SPENDING OVERVIEW:")
        print(f"💰 Total Spending: ₹{report['spending_analysis']['total_spending']:.0f}")
        print(f"📱 Transactions: {report['spending_analysis']['transaction_count']}")
        print(f"💳 Average Transaction: ₹{report['spending_analysis']['avg_transaction']:.0f}")
        print(f"🎯 Financial Health: {report['financial_health_score']}/100")
        
        print(f"\n🏆 TOP SPENDING CATEGORIES:")
        for i, category in enumerate(report['spending_analysis']['top_spending_categories'][:3], 1):
            cat_data = report['spending_analysis']['spending_by_category'][category]
            print(f"{i}. {category}: ₹{cat_data['amount']:.0f} ({cat_data['percentage']}%) - {cat_data['transactions']} transactions")
        
        if report['anomaly_summary']['total_anomalies'] > 0:
            print(f"\n🚨 ANOMALY SUMMARY:")
            print(f"Total Anomalies: {report['anomaly_summary']['total_anomalies']}")
            print(f"High Priority: {report['anomaly_summary']['high_priority']}")
            if report['anomaly_summary']['categories_affected']:
                print(f"Categories: {', '.join(report['anomaly_summary']['categories_affected'])}")
        
        # Display AI advice
        print(f"\n" + "="*70)
        print("🤖 PERSONALIZED FINANCIAL ADVICE")
        print("="*70)
        print(report['ai_advice'])
        
        print(f"\n" + "="*70)
        print("💡 QUICK SUMMARY")
        print("="*70)
        print(f"💰 Potential Monthly Savings: ₹{report['recommendations']['total_savings_potential']:.0f}")
        print(f"🎯 Focus Area: {report['recommendations']['top_optimization_category']}")
        print(f"🏦 Emergency Fund Target: ₹{report['recommendations']['emergency_fund_target']:.0f}")
        print(f"💾 Ideal Monthly Savings: ₹{report['recommendations']['budget_allocation']['savings_budget']:.0f}")
        
        print(f"\n✅ DEMO COMPLETED SUCCESSFULLY!")
        print("="*70)
        
        return report
        
    except Exception as e:
        print(f"❌ Error during AI advisor demo: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("🤖 FinCoach AI Financial Advisor - Simplified Version")
    print("   Generating intelligent financial advice...")
    
    # Run the demo
    report = demo_ai_advisor()
    
    if report:
        print("\n" + "="*50)
        print("✅ AI FINANCIAL ADVISOR MODULE READY!")
        print("="*50)
        print("\nIntegration examples:")
        print("from ai_financial_advisor import FinancialAdvisor")
        print("advisor = FinancialAdvisor()")
        print("report = advisor.create_comprehensive_report(classified_data)")
        print("\nNo external API keys required! 🎉")
    else:
        print("\n❌ Demo failed. Check your setup and try again.")
