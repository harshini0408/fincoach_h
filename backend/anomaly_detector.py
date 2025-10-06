"""
FinCoach Anomaly Detection System
Detects unusual spending patterns and budget violations
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')


class SpendingAnomalyDetector:
    """
    Advanced Anomaly Detection for Personal Finance
    
    Features:
    - Statistical anomaly detection (Z-scores, rolling averages)
    - ML-based detection (Isolation Forest, LOF)
    - Category-wise spending analysis
    - Trend-based anomaly detection
    - Budget violation alerts
    """
    
    def __init__(self):
        self.user_baselines = {}  # Store user spending baselines
        self.category_thresholds = {}  # Category-specific thresholds
        self.ml_detectors = {}  # ML models per user
        self.is_initialized = False
        
        # Default anomaly thresholds
        self.default_thresholds = {
            'z_score_threshold': 2.0,  # 2 standard deviations
            'percentage_threshold': 50,  # 50% increase from average
            'isolation_contamination': 0.1,  # 10% of data considered anomalous
            'lof_contamination': 0.1
        }
    
    def establish_user_baseline(self, user_transactions_df, user_id=None):
        """
        Establish spending baselines for a user based on historical data
        
        Args:
            user_transactions_df (DataFrame): User's historical transactions
            user_id (str): User identifier
            
        Returns:
            dict: User spending baseline statistics
        """
        print(f"\n📊 Establishing spending baseline for user...")
        
        if user_id is None:
            user_id = 'default_user'
        
        # Check if we have the required column
        category_col = 'predicted_category' if 'predicted_category' in user_transactions_df.columns else 'category'
        
        if category_col not in user_transactions_df.columns:
            print("⚠️  No category column found. Please run expense classification first!")
            return None
        
        # Add time features
        df = user_transactions_df.copy()
        df['date'] = pd.to_datetime(df['date'])
        df['week'] = df['date'].dt.isocalendar().week
        df['month'] = df['date'].dt.month
        df['day_of_week'] = df['date'].dt.dayofweek
        
        baseline = {
            'user_id': user_id,
            'total_transactions': len(df),
            'date_range': {
                'start': df['date'].min(),
                'end': df['date'].max(),
                'days': (df['date'].max() - df['date'].min()).days
            },
            'category_stats': {},
            'temporal_patterns': {},
            'spending_distribution': {}
        }
        
        # Category-wise baseline statistics
        for category in df[category_col].unique():
            category_data = df[df[category_col] == category]
            
            # Weekly spending analysis
            weekly_spending = category_data.groupby(['week'])['amount'].sum()
            
            if len(weekly_spending) > 0:
                baseline['category_stats'][category] = {
                    'mean_weekly': weekly_spending.mean(),
                    'std_weekly': max(weekly_spending.std(), 100),  # Minimum std to avoid division by zero
                    'median_weekly': weekly_spending.median(),
                    'max_weekly': weekly_spending.max(),
                    'min_weekly': weekly_spending.min(),
                    'transaction_count': len(category_data),
                    'avg_transaction_amount': category_data['amount'].mean(),
                    'total_spent': category_data['amount'].sum()
                }
        
        # Overall spending patterns
        weekly_total = df.groupby(['week'])['amount'].sum()
        baseline['spending_distribution'] = {
            'mean_weekly_total': weekly_total.mean(),
            'std_weekly_total': max(weekly_total.std(), 500),  # Minimum std
            'median_weekly_total': weekly_total.median(),
            'percentile_75': weekly_total.quantile(0.75),
            'percentile_90': weekly_total.quantile(0.90)
        }
        
        # Temporal patterns
        daily_spending = df.groupby(['day_of_week'])['amount'].mean()
        weekend_avg = daily_spending[5:].mean() if len(daily_spending) > 5 else daily_spending.mean()
        weekday_avg = daily_spending[:5].mean() if len(daily_spending) > 5 else daily_spending.mean()
        
        baseline['temporal_patterns'] = {
            'daily_avg_spending': daily_spending.to_dict(),
            'weekend_vs_weekday_ratio': weekend_avg / weekday_avg if weekday_avg > 0 else 1.0
        }
        
        # Store baseline
        self.user_baselines[user_id] = baseline
        self.is_initialized = True
        
        print(f"✅ Baseline established for {len(df)} transactions")
        print(f"   Date range: {baseline['date_range']['start'].date()} to {baseline['date_range']['end'].date()}")
        print(f"   Categories: {list(baseline['category_stats'].keys())}")
        
        return baseline
    
    def detect_statistical_anomalies(self, current_period_data, user_id='default_user'):
        """
        Detect anomalies using statistical methods (Z-scores, percentage changes)
        
        Args:
            current_period_data (DataFrame): Recent transactions to analyze
            user_id (str): User identifier
            
        Returns:
            dict: Detected anomalies with severity and explanations
        """
        if user_id not in self.user_baselines:
            return {"error": "No baseline established for this user. Run establish_user_baseline() first."}
        
        baseline = self.user_baselines[user_id]
        anomalies = []
        
        print(f"\n🔍 Detecting statistical anomalies...")
        
        # Prepare current period data
        df = current_period_data.copy()
        df['date'] = pd.to_datetime(df['date'])
        
        # Check for category column
        category_col = 'predicted_category' if 'predicted_category' in df.columns else 'category'
        
        # Category-wise anomaly detection
        current_category_spending = df.groupby(category_col)['amount'].sum()
        
        for category, current_spending in current_category_spending.items():
            if category in baseline['category_stats']:
                category_baseline = baseline['category_stats'][category]
                
                # Z-score anomaly detection
                mean_weekly = category_baseline['mean_weekly']
                std_weekly = category_baseline['std_weekly']
                
                z_score = (current_spending - mean_weekly) / std_weekly
                
                # Percentage change anomaly detection
                percentage_change = ((current_spending - mean_weekly) / mean_weekly) * 100 if mean_weekly > 0 else 0
                
                # Detect anomalies
                if abs(z_score) > self.default_thresholds['z_score_threshold']:
                    severity = 'high' if abs(z_score) > 3 else 'medium'
                    anomaly_type = 'spike' if z_score > 0 else 'drop'
                    
                    anomalies.append({
                        'type': 'statistical',
                        'category': category,
                        'anomaly_type': anomaly_type,
                        'severity': severity,
                        'current_amount': round(current_spending, 2),
                        'expected_amount': round(mean_weekly, 2),
                        'z_score': round(z_score, 2),
                        'percentage_change': round(percentage_change, 1),
                        'explanation': f"You spent ₹{current_spending:.0f} on {category} this period, which is {abs(percentage_change):.0f}% {'above' if z_score > 0 else 'below'} your usual ₹{mean_weekly:.0f}",
                        'detection_method': 'z_score'
                    })
        
        # Overall spending anomaly
        current_total = df['amount'].sum()
        expected_total = baseline['spending_distribution']['mean_weekly_total']
        std_total = baseline['spending_distribution']['std_weekly_total']
        total_z_score = (current_total - expected_total) / std_total
        
        if abs(total_z_score) > self.default_thresholds['z_score_threshold']:
            total_percentage_change = ((current_total - expected_total) / expected_total) * 100 if expected_total > 0 else 0
            
            anomalies.append({
                'type': 'statistical',
                'category': 'Overall',
                'anomaly_type': 'total_spending_' + ('spike' if total_z_score > 0 else 'drop'),
                'severity': 'high' if abs(total_z_score) > 3 else 'medium',
                'current_amount': round(current_total, 2),
                'expected_amount': round(expected_total, 2),
                'z_score': round(total_z_score, 2),
                'percentage_change': round(total_percentage_change, 1),
                'explanation': f"Your total spending of ₹{current_total:.0f} is {abs(total_percentage_change):.0f}% {'higher' if total_z_score > 0 else 'lower'} than your usual ₹{expected_total:.0f}",
                'detection_method': 'total_spending_z_score'
            })
        
        print(f"   Found {len(anomalies)} statistical anomalies")
        return {
            'anomalies': anomalies,
            'summary': {
                'total_anomalies': len(anomalies),
                'high_severity': len([a for a in anomalies if a['severity'] == 'high']),
                'medium_severity': len([a for a in anomalies if a['severity'] == 'medium']),
                'categories_affected': list(set([a['category'] for a in anomalies]))
            }
        }
    
    def detect_ml_anomalies(self, user_transactions_df, user_id='default_user'):
        """
        Detect anomalies using machine learning methods
        
        Args:
            user_transactions_df (DataFrame): User's transaction data
            user_id (str): User identifier
            
        Returns:
            dict: ML-detected anomalies
        """
        print(f"\n🤖 Detecting ML-based anomalies...")
        
        df = user_transactions_df.copy()
        
        if len(df) < 10:
            print("   ⚠️ Not enough data for ML anomaly detection (need at least 10 transactions)")
            return {'anomalies': [], 'summary': {'total_ml_anomalies': 0}}
        
        # Feature engineering for ML
        df['date'] = pd.to_datetime(df['date'])
        df['day_of_week'] = df['date'].dt.dayofweek
        df['month'] = df['date'].dt.month
        
        # Check for category column
        category_col = 'predicted_category' if 'predicted_category' in df.columns else 'category'
        
        # One-hot encode categories
        category_dummies = pd.get_dummies(df[category_col], prefix='cat')
        
        # Combine features
        feature_matrix = pd.concat([
            df[['amount', 'day_of_week', 'month']],
            category_dummies
        ], axis=1)
        
        # Handle missing values
        feature_matrix = feature_matrix.fillna(0)
        
        # Standardize features
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(feature_matrix)
        
        anomalies = []
        
        try:
            # Isolation Forest
            iso_forest = IsolationForest(
                contamination=min(self.default_thresholds['isolation_contamination'], 0.3),
                random_state=42,
                n_estimators=50
            )
            
            iso_predictions = iso_forest.fit_predict(features_scaled)
            iso_scores = iso_forest.decision_function(features_scaled)
            
            # Extract anomalies
            df['iso_anomaly'] = iso_predictions == -1
            df['iso_score'] = iso_scores
            
            # Isolation Forest anomalies
            iso_anomalies = df[df['iso_anomaly']]
            for _, row in iso_anomalies.iterrows():
                anomalies.append({
                    'type': 'ml',
                    'detection_method': 'isolation_forest',
                    'transaction_date': row['date'].strftime('%Y-%m-%d'),
                    'category': row[category_col],
                    'amount': round(row['amount'], 2),
                    'description': row['description'],
                    'anomaly_score': round(row['iso_score'], 3),
                    'severity': 'high' if row['iso_score'] < -0.5 else 'medium',
                    'explanation': f"Unusual transaction pattern detected: ₹{row['amount']:.0f} spent on {row[category_col]} - {row['description'][:50]}..."
                })
            
            print(f"   Isolation Forest: {len(iso_anomalies)} anomalies")
            
        except Exception as e:
            print(f"   ⚠️ ML anomaly detection error: {str(e)}")
        
        print(f"   Found {len(anomalies)} ML anomalies")
        
        return {
            'anomalies': anomalies,
            'summary': {
                'total_ml_anomalies': len(anomalies),
                'isolation_forest_count': len([a for a in anomalies if a['detection_method'] == 'isolation_forest']),
                'high_severity': len([a for a in anomalies if a['severity'] == 'high']),
                'medium_severity': len([a for a in anomalies if a['severity'] == 'medium'])
            }
        }
    
    def create_spending_insights(self, user_transactions_df, user_id='default_user'):
        """
        Create detailed spending insights and patterns
        
        Args:
            user_transactions_df (DataFrame): User's transaction data
            user_id (str): User identifier
            
        Returns:
            dict: Spending insights and patterns
        """
        df = user_transactions_df.copy()
        df['date'] = pd.to_datetime(df['date'])
        
        category_col = 'predicted_category' if 'predicted_category' in df.columns else 'category'
        
        insights = {
            'spending_trends': {},
            'category_analysis': {},
            'temporal_patterns': {},
            'budget_recommendations': {}
        }
        
        # Category analysis
        for category in df[category_col].unique():
            category_data = df[df[category_col] == category]
            
            insights['category_analysis'][category] = {
                'total_spent': round(category_data['amount'].sum(), 2),
                'transaction_count': len(category_data),
                'avg_transaction': round(category_data['amount'].mean(), 2),
                'max_transaction': round(category_data['amount'].max(), 2),
                'spending_frequency': len(category_data) / len(df) * 100
            }
        
        # Temporal patterns
        daily_spending = df.groupby(df['date'].dt.dayofweek)['amount'].mean()
        monthly_spending = df.groupby(df['date'].dt.month)['amount'].sum()
        
        insights['temporal_patterns'] = {
            'daily_average': {f'day_{i}': round(daily_spending.get(i, 0), 2) for i in range(7)},
            'monthly_totals': {f'month_{i}': round(monthly_spending.get(i, 0), 2) for i in range(1, 13)},
            'weekend_vs_weekday': {
                'weekend_avg': round(daily_spending[5:].mean(), 2),
                'weekday_avg': round(daily_spending[:5].mean(), 2)
            }
        }
        
        return insights
    
    def generate_anomaly_report(self, user_transactions_df, current_period_data=None, user_id='default_user'):
        """
        Generate comprehensive anomaly detection report
        
        Args:
            user_transactions_df (DataFrame): Historical transactions
            current_period_data (DataFrame): Recent period to analyze (optional)
            user_id (str): User identifier
            
        Returns:
            dict: Complete anomaly analysis report
        """
        print(f"\n📋 Generating Anomaly Detection Report")
        print("="*50)
        
        # Establish baseline if not already done
        if user_id not in self.user_baselines:
            baseline_result = self.establish_user_baseline(user_transactions_df, user_id)
            if baseline_result is None:
                return {"error": "Could not establish baseline. Check your data format."}
        
        report = {
            'user_id': user_id,
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'statistical_anomalies': {},
            'ml_anomalies': {},
            'spending_insights': {},
            'combined_insights': {},
            'recommendations': []
        }
        
        # Statistical anomaly detection
        if current_period_data is not None and len(current_period_data) > 0:
            stat_results = self.detect_statistical_anomalies(current_period_data, user_id)
            report['statistical_anomalies'] = stat_results
        else:
            # Use last 20% of data as current period for demo
            split_index = int(len(user_transactions_df) * 0.8)
            current_data = user_transactions_df.iloc[split_index:]
            if len(current_data) > 0:
                stat_results = self.detect_statistical_anomalies(current_data, user_id)
                report['statistical_anomalies'] = stat_results
        
        # ML-based anomaly detection on full dataset
        ml_results = self.detect_ml_anomalies(user_transactions_df, user_id)
        report['ml_anomalies'] = ml_results
        
        # Spending insights
        insights = self.create_spending_insights(user_transactions_df, user_id)
        report['spending_insights'] = insights
        
        # Combine insights
        all_anomalies = []
        if 'anomalies' in report['statistical_anomalies']:
            all_anomalies.extend(report['statistical_anomalies']['anomalies'])
        if 'anomalies' in report['ml_anomalies']:
            all_anomalies.extend(report['ml_anomalies']['anomalies'])
        
        # Generate recommendations
        recommendations = self.generate_recommendations(all_anomalies)
        report['recommendations'] = recommendations
        
        # Summary
        report['combined_insights'] = {
            'total_anomalies_detected': len(all_anomalies),
            'high_priority_anomalies': len([a for a in all_anomalies if a.get('severity') == 'high']),
            'categories_with_anomalies': list(set([a.get('category', 'Unknown') for a in all_anomalies])),
            'most_anomalous_category': self.get_most_anomalous_category(all_anomalies),
            'anomaly_detection_methods_used': list(set([a.get('detection_method', 'unknown') for a in all_anomalies]))
        }
        
        print(f"✅ Report generated: {report['combined_insights']['total_anomalies_detected']} anomalies detected")
        
        return report
    
    def generate_recommendations(self, anomalies):
        """Generate actionable recommendations based on detected anomalies"""
        recommendations = []
        
        # High spending recommendations
        high_spending_anomalies = [a for a in anomalies if a.get('anomaly_type') == 'spike']
        if high_spending_anomalies:
            for anomaly in high_spending_anomalies[:3]:  # Top 3
                current_amt = anomaly.get('current_amount', 0)
                expected_amt = anomaly.get('expected_amount', 0)
                overspend = current_amt - expected_amt
                
                recommendations.append({
                    'type': 'budget_alert',
                    'priority': 'high',
                    'category': anomaly.get('category', 'Unknown'),
                    'message': f"Consider reducing {anomaly.get('category', 'this category')} spending. You're ₹{overspend:.0f} over your usual budget.",
                    'action': f"Try to limit {anomaly.get('category', 'spending')} to ₹{expected_amt:.0f} next period."
                })
        
        # ML anomaly recommendations
        ml_anomalies = [a for a in anomalies if a.get('type') == 'ml']
        if ml_anomalies:
            recommendations.append({
                'type': 'pattern_alert',
                'priority': 'medium',
                'message': f"We detected {len(ml_anomalies)} unusual transactions. Review these to ensure they're legitimate.",
                'action': "Check your recent transactions for any unauthorized or mistaken payments."
            })
        
        # General recommendation
        if len(anomalies) > 5:
            recommendations.append({
                'type': 'general_advice',
                'priority': 'medium',
                'message': "Your spending pattern shows several unusual activities. Consider setting up budget alerts.",
                'action': "Set monthly budgets for each category to get notified when you approach limits."
            })
        elif len(anomalies) == 0:
            recommendations.append({
                'type': 'positive_feedback',
                'priority': 'low',
                'message': "Great job! Your spending patterns look consistent and healthy.",
                'action': "Keep up the good financial habits and continue monitoring your expenses."
            })
        
        return recommendations
    
    def get_most_anomalous_category(self, anomalies):
        """Find the category with the most anomalies"""
        if not anomalies:
            return None
        
        category_counts = {}
        for anomaly in anomalies:
            cat = anomaly.get('category', 'Unknown')
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        return max(category_counts, key=category_counts.get) if category_counts else None


# =====================================================================
# TESTING AND DEMO FUNCTIONS
# =====================================================================

def demo_anomaly_detection():
    """Demo the anomaly detection system with the dataset"""
    print("\n" + "="*70)
    print("FINCOACH ANOMALY DETECTION SYSTEM - DEMO")
    print("="*70)
    
    try:
        # Load the dataset
        transactions_df = pd.read_csv('expenses_dataset.csv')
        print(f"✅ Loaded {len(transactions_df)} transactions from expenses_dataset.csv")
        
        # Initialize detector
        detector = SpendingAnomalyDetector()
        
        # Generate anomaly report
        report = detector.generate_anomaly_report(transactions_df)
        
        # Display results
        print(f"\n📊 ANOMALY DETECTION RESULTS:")
        print(f"Total anomalies detected: {report['combined_insights']['total_anomalies_detected']}")
        print(f"High priority: {report['combined_insights']['high_priority_anomalies']}")
        print(f"Categories affected: {report['combined_insights']['categories_with_anomalies']}")
        
        # Show some example anomalies
        all_anomalies = []
        if 'anomalies' in report.get('statistical_anomalies', {}):
            all_anomalies.extend(report['statistical_anomalies']['anomalies'])
        if 'anomalies' in report.get('ml_anomalies', {}):
            all_anomalies.extend(report['ml_anomalies']['anomalies'][:3])  # Show first 3 ML anomalies
        
        if all_anomalies:
            print(f"\n🚨 TOP ANOMALIES:")
            for i, anomaly in enumerate(all_anomalies[:5], 1):
                print(f"\n{i}. {anomaly.get('severity', 'medium').upper()} SEVERITY")
                print(f"   Category: {anomaly.get('category', 'Unknown')}")
                print(f"   {anomaly.get('explanation', 'Unusual pattern detected')}")
                print(f"   Method: {anomaly.get('detection_method', 'unknown')}")
        
        # Show recommendations
        if report['recommendations']:
            print(f"\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"\n{i}. {rec['message']}")
                print(f"   Action: {rec['action']}")
        
        print(f"\n🎉 Demo completed successfully!")
        return report
        
    except FileNotFoundError:
        print("❌ Error: expenses_dataset.csv not found!")
        print("   Make sure the file is in the same directory as this script.")
        return None
    except Exception as e:
        print(f"❌ Error during demo: {str(e)}")
        return None


def test_with_classified_data():
    """Test with pre-classified expense data"""
    try:
        from expense_classifier import ExpenseClassifier
        
        print("\n🔄 Testing with classified expense data...")
        
        # Load and classify data first
        transactions_df = pd.read_csv('expenses_dataset.csv')
        
        # Check if model exists
        import os
        if os.path.exists('expense_classifier_model.pkl'):
            classifier = ExpenseClassifier()
            classifier.load_model('expense_classifier_model.pkl')
            classified_df = classifier.classify_batch(transactions_df)
        else:
            print("   Using existing categories from dataset...")
            classified_df = transactions_df.copy()
            classified_df['predicted_category'] = classified_df['category']
        
        # Run anomaly detection
        detector = SpendingAnomalyDetector()
        report = detector.generate_anomaly_report(classified_df)
        
        print(f"✅ Successfully detected {report['combined_insights']['total_anomalies_detected']} anomalies")
        
        return report
        
    except ImportError:
        print("   ⚠️ expense_classifier not found, using basic demo...")
        return demo_anomaly_detection()
    except Exception as e:
        print(f"   ⚠️ Error: {str(e)}")
        return demo_anomaly_detection()


if __name__ == "__main__":
    print("🚨 FinCoach Anomaly Detection System")
    print("   Testing with your expense dataset...")
    
    # Run the demo
    report = test_with_classified_data()
    
    if report:
        print("\n" + "="*50)
        print("✅ ANOMALY DETECTION MODULE READY!")
        print("="*50)
        print("\nIntegration examples:")
        print("from anomaly_detector import SpendingAnomalyDetector")
        print("detector = SpendingAnomalyDetector()")
        print("report = detector.generate_anomaly_report(your_data)")
    else:
        print("\n❌ Demo failed. Check your setup and try again.")
