# expense_classifier_improved.py
"""
Improved FinCoach Expense Classifier
- Merchant normalization + fuzzy matching
- Rule-first + ML fallback
- Explainable reasons for predictions
- Active-learning logging of low-confidence cases
- Optional hierarchical subcategory support
"""

import re
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np
import joblib

from rapidfuzz import fuzz, process

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

# ---------- Configuration ----------
LOW_CONFIDENCE_THRESHOLD = 0.60   # below this -> logged for review
FUZZY_MATCH_THRESHOLD = 85        # 0-100 fuzzy ratio threshold
TOP_TFIDF_TOKENS = 5              # tokens to return as explanation
REVIEW_CSV = "review_queue.csv"
MODEL_FILE_DEFAULT = "expense_classifier_improved.pkl"
# -----------------------------------

class ExpenseClassifierImproved:
    def __init__(self):
        # Merchant rules mapping: canonical merchant substrings -> (category, optional subcategory)
        # high_priority are checked exact substring presence first; medium are softer matches
        self.merchant_rules = {
            'Food': {
                'high_priority': ['zomato', 'swiggy', 'dominos', 'mcdonald', 'kfc', 'subway', 'pizza hut', 'burger king'],
                'medium_priority': ['dunzo', 'bigbasket', 'grofers', 'grocery', 'restaurant', 'cafe', 'dine', 'eat']
            },
            'Travel': {
                'high_priority': ['uber', 'ola', 'rapido', 'irctc', 'redbus', 'makemytrip', 'goibibo'],
                'medium_priority': ['metro', 'taxi', 'cab', 'bus', 'train', 'flight', 'hotel', 'booking']
            },
            'Shopping': {
                'high_priority': ['amazon', 'flipkart', 'myntra', 'ajio', 'nykaa', 'meesho', 'snapdeal'],
                'medium_priority': ['decathlon', 'mall', 'store', 'shopping', 'retail', 'mart']
            },
            'Bills': {
                'high_priority': ['airtel', 'jio', 'bsnl', 'vodafone', 'tneb', 'bescom', 'torrent'],
                'medium_priority': ['electricity', 'water', 'gas', 'internet', 'mobile', 'recharge', 'bill']
            },
            'Subscriptions': {
                'high_priority': ['netflix', 'youtube premium', 'disney+', 'spotify', 'hotstar', 'prime video', 'amazon prime'],
                'medium_priority': ['subscription', 'monthly', 'annual', 'membership']
            },
            'Others': {
                'high_priority': ['hospital', 'pharmacy', 'medical', 'insurance', 'doctor'],
                'medium_priority': ['topup', 'wallet', 'donation', 'misc', 'miscellaneous']
            }
        }

        # Optional merchant -> subcategory map for fine-grain output
        self.merchant_to_subcategory = {
            'zomato': ('Food', 'Delivery'),
            'swiggy': ('Food', 'Delivery'),
            'bigbasket': ('Food', 'Groceries'),
            'amazon': ('Shopping', 'Online Shopping'),
            'flipkart': ('Shopping', 'Online Shopping'),
            'netflix': ('Subscriptions', 'Entertainment'),
            'spotify': ('Subscriptions', 'Entertainment'),
            'uber': ('Travel', 'Cab'),
            'ola': ('Travel', 'Cab'),
            'tneb': ('Bills', 'Electricity'),
            'airtel': ('Bills', 'Mobile')
        }

        # Pre-build merchant lookup list for fuzzy matching (combine high & medium)
        self._merchant_corpus = self._build_merchant_corpus()

        # ML pipeline placeholders
        self.ml_pipeline: Optional[Pipeline] = None
        self.label_list: Optional[List[str]] = None
        self.is_trained = False

    # --------------------------
    # Normalization / Preprocess
    # --------------------------
    @staticmethod
    def normalize_description(desc: str) -> str:
        """Clean and normalize: lowercase, remove UPI/MMID tokens, txn ids, punctuation."""
        if pd.isna(desc):
            return ""
        s = str(desc).lower()
        # Remove common UPI / bank tokens: things like @oksbi, @okhdfcbank, upi references, ref/txn numbers
        s = re.sub(r'@\w+', ' ', s)  # remove @bank tags
        s = re.sub(r'upi[\w\-/]*', ' ', s)
        s = re.sub(r'txn[:#]?\s*\w+', ' ', s)
        s = re.sub(r'transaction\s*\w+', ' ', s)
        s = re.sub(r'\bref[:#]?\s*\w+', ' ', s)
        s = re.sub(r'[\d]{4,}', ' ', s)  # remove long numbers (ids)
        s = re.sub(r'[^a-z0-9\s]', ' ', s)  # keep alphanumeric and spaces
        s = ' '.join(s.split())
        return s

    def _build_merchant_corpus(self) -> List[str]:
        corpus = []
        for cat, groups in self.merchant_rules.items():
            corpus.extend(groups.get('high_priority', []))
            corpus.extend(groups.get('medium_priority', []))
        # Remove duplicates & sort by length desc so longer names score better in fuzzy process
        corpus = sorted(list(set(corpus)), key=lambda x: -len(x))
        return corpus

    # --------------------------
    # Rule-based classification
    # --------------------------
    def _rule_match(self, normalized_desc: str) -> Dict[str, Any]:
        """
        Returns best rule match if any, plus score and matched merchant.
        """
        scores = {}
        matched_terms = []

        for category, groups in self.merchant_rules.items():
            score = 0
            for m in groups.get('high_priority', []):
                if m in normalized_desc:
                    score += 3
                    matched_terms.append((category, m, 'high'))
            for m in groups.get('medium_priority', []):
                if m in normalized_desc:
                    score += 1
                    matched_terms.append((category, m, 'medium'))
            if score > 0:
                scores[category] = score

        if not scores:
            return {'match': None}

        best_cat = max(scores, key=scores.get)
        best_score = scores[best_cat]
        # Normalize confidence: assume max possible from a single high_priority match is 3
        confidence = min(1.0, best_score / 3.0)
        # Find matched merchant names for reasoning
        matched = [m for (c, m, p) in matched_terms if c == best_cat]
        return {
            'match': best_cat,
            'merchant_matches': matched,
            'confidence': confidence,
            'score': best_score
        }

    # --------------------------
    # Fuzzy matching
    # --------------------------
    def _fuzzy_merchant_match(self, normalized_desc: str) -> Optional[Dict[str, Any]]:
        """
        Use fuzzy matching to find best merchant in corpus.
        Returns a dict with merchant and fuzzy score if above threshold.
        """
        # Use rapidfuzz process.extractOne
        best = process.extractOne(normalized_desc, self._merchant_corpus, scorer=fuzz.partial_ratio)
        if best:
            merchant, score, _ = best  # tuple: (match_string, score, index)
            if score >= FUZZY_MATCH_THRESHOLD:
                # Determine category for this merchant by searching in merchant_rules
                for cat, groups in self.merchant_rules.items():
                    if merchant in groups.get('high_priority', []) or merchant in groups.get('medium_priority', []):
                        return {'merchant': merchant, 'score': score, 'category': cat}
                # If not found (rare), return merchant only
                return {'merchant': merchant, 'score': score, 'category': None}
        return None

    # --------------------------
    # ML: training & explain helpers
    # --------------------------
    def train_ml_model(self, df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42) -> Dict[str, Any]:
        """
        Train TF-IDF + MultinomialNB model on labeled data.
        Expects df to have 'description' and 'category' columns.
        Returns metrics dict.
        """
        print("Starting ML training...")
        df = df.copy()
        df['normalized'] = df['description'].apply(self.normalize_description)
        X = df['normalized']
        y = df['category']

        y = y.astype(str)          # Convert all categories to strings
        y = y.fillna("Others")     # Replace missing categories with 'Others'
        self.label_list = sorted(y.unique().tolist())


        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size,
                                                            random_state=random_state, stratify=y)

        self.ml_pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(max_features=2000, ngram_range=(1, 2), stop_words='english')),
            ('clf', MultinomialNB(alpha=0.1))
        ])

        self.ml_pipeline.fit(X_train, y_train)
        y_pred = self.ml_pipeline.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        print(f"ML training complete — Accuracy: {acc:.4f}")
        print("Classification report:\n", classification_report(y_test, y_pred))
        self.is_trained = True
        return {'accuracy': acc, 'train_samples': len(X_train), 'test_samples': len(X_test)}

    def get_top_tfidf_tokens(self, text: str, top_n: int = TOP_TFIDF_TOKENS) -> List[str]:
        """
        Return top TF-IDF tokens for a single text to help explain ML prediction.
        """
        if not self.is_trained or self.ml_pipeline is None:
            return []

        tfidf: TfidfVectorizer = self.ml_pipeline.named_steps['tfidf']
        vect = tfidf.transform([text])
        feature_array = np.array(tfidf.get_feature_names_out())
        tfidf_sorting = np.argsort(vect.toarray()).flatten()[::-1]
        top_n_idx = tfidf_sorting[:top_n]
        top_tokens = feature_array[top_n_idx].tolist()
        # filter out empty tokens
        return [t for t in top_tokens if t.strip()]

    # --------------------------
    # Prediction APIs
    # --------------------------
    def predict_single(self, description: str, amount: float = None) -> Dict[str, Any]:
        """
        Predict category for a single transaction. Returns dict:
        {
          category, confidence, method ('rule-based'|'fuzzy'|'ml'|'default'),
          reasons: [str], subcategory (optional)
        }
        """
        reasons = []
        norm = self.normalize_description(description)

        # 1) Rule-based exact substring matching
        rule = self._rule_match(norm)
        if rule.get('match'):
            cat = rule['match']
            confidence = rule['confidence']
            reasons.append(f"rule_merchant_match: {','.join(rule.get('merchant_matches',[]))}")
            # find subcategory if known
            subcat = None
            for m in rule.get('merchant_matches', []):
                if m in self.merchant_to_subcategory:
                    subcat = self.merchant_to_subcategory[m][1]
                    break
            # If rule confidence high enough, return immediately
            if confidence >= 0.80:
                return {'category': cat, 'confidence': round(confidence, 3), 'method': 'rule-based', 'reasons': reasons, 'subcategory': subcat}

        # 2) Fuzzy merchant matching
        fuzzy = self._fuzzy_merchant_match(norm)
        if fuzzy:
            reasons.append(f"fuzzy_merchant_match: {fuzzy['merchant']} (score={fuzzy['score']})")
            if fuzzy.get('category'):
                subcat = None
                if fuzzy['merchant'] in self.merchant_to_subcategory:
                    subcat = self.merchant_to_subcategory[fuzzy['merchant']][1]
                # treat fuzzy match with high score as confident
                if fuzzy['score'] >= 92:
                    return {'category': fuzzy['category'], 'confidence': round(fuzzy['score'] / 100.0, 3),
                            'method': 'fuzzy', 'reasons': reasons, 'subcategory': subcat}
                # otherwise we keep reason but allow ML fallback

        # 3) ML fallback
        if self.is_trained and self.ml_pipeline is not None:
            ml_input = norm
            pred = self.ml_pipeline.predict([ml_input])[0]
            probs = self.ml_pipeline.predict_proba([ml_input])[0]
            conf = float(probs.max())
            reasons.append(f"ml_top_tokens: {', '.join(self.get_top_tfidf_tokens(ml_input, top_n=TOP_TFIDF_TOKENS))}")
            # attach subcategory if merchant known
            matched_sub = None
            for k, v in self.merchant_to_subcategory.items():
                if k in norm:
                    matched_sub = v[1]
                    break
            result = {'category': str(pred), 'confidence': round(conf, 3), 'method': 'ml', 'reasons': reasons, 'subcategory': matched_sub}
            # Active learning hook: log if low confidence
            if conf < LOW_CONFIDENCE_THRESHOLD:
                self._log_for_review(description, amount, result)
            return result

        # 4) Default fallback
        fallback = {'category': 'Others', 'confidence': 0.5, 'method': 'default', 'reasons': ['fallback_default'], 'subcategory': None}
        # Log fallback for review to improve model
        self._log_for_review(description, amount, fallback)
        return fallback

    def classify_batch(self, transactions_df: pd.DataFrame) -> pd.DataFrame:
        """
        Batch classify DataFrame with columns at least ['description','amount','date' optional].
        Returns DataFrame with added fields: predicted_category, confidence, method, reasons, subcategory, actual_category (if present), correct (if actual present)
        """
        rows = []
        for _, r in transactions_df.iterrows():
            desc = r.get('description', '')
            amt = r.get('amount', None)
            pred = self.predict_single(desc, amt)
            row = {
                'date': r.get('date'),
                'description': desc,
                'amount': amt,
                'predicted_category': pred['category'],
                'confidence': pred['confidence'],
                'method': pred['method'],
                'reasons': '; '.join(pred.get('reasons', [])),
                'subcategory': pred.get('subcategory')
            }
            if 'category' in r:
                row['actual_category'] = r['category']
                row['correct'] = (row['actual_category'] == row['predicted_category'])
            rows.append(row)
        return pd.DataFrame(rows)

    # --------------------------
    # Active learning: logging
    # --------------------------
    def _log_for_review(self, description: str, amount: float, prediction: Dict[str, Any]):
        """
        Append low-confidence or fallback predictions to a CSV for human review.
        """
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'description': description,
            'amount': amount,
            'predicted_category': prediction.get('category'),
            'confidence': prediction.get('confidence'),
            'method': prediction.get('method'),
            'reasons': '; '.join(prediction.get('reasons', []))
        }
        df_new = pd.DataFrame([entry])
        if os.path.exists(REVIEW_CSV):
            df_new.to_csv(REVIEW_CSV, mode='a', header=False, index=False)
        else:
            df_new.to_csv(REVIEW_CSV, index=False)
        print(f"[review] Logged low-confidence case (conf={entry['confidence']}) to {REVIEW_CSV}")

    # --------------------------
    # Save / Load model
    # --------------------------
    def save_model(self, filepath: str = MODEL_FILE_DEFAULT):
        """
        Save ML pipeline and metadata (merchant rules, subcategory map) to disk.
        """
        data = {
            'ml_pipeline': self.ml_pipeline,
            'merchant_rules': self.merchant_rules,
            'merchant_to_subcategory': self.merchant_to_subcategory
        }
        joblib.dump(data, filepath)
        print(f"Saved model to {filepath}")

    def load_model(self, filepath: str = MODEL_FILE_DEFAULT):
        """
        Load model and metadata from disk.
        """
        data = joblib.load(filepath)
        self.ml_pipeline = data.get('ml_pipeline')
        self.merchant_rules = data.get('merchant_rules', self.merchant_rules)
        self.merchant_to_subcategory = data.get('merchant_to_subcategory', self.merchant_to_subcategory)
        self._merchant_corpus = self._build_merchant_corpus()
        self.is_trained = self.ml_pipeline is not None
        print(f"Loaded model from {filepath}; trained={self.is_trained}")

    # --------------------------
    # Utility methods
    # --------------------------
    def get_spending_summary(self, classified_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Return category-wise spending summary from the classified dataframe (result of classify_batch).
        """
        total = classified_df['amount'].sum() if 'amount' in classified_df.columns else 0.0
        summary = {}
        for cat in classified_df['predicted_category'].unique():
            group = classified_df[classified_df['predicted_category'] == cat]
            total_spent = group['amount'].sum()
            summary[cat] = {
                'total_spent': round(total_spent, 2),
                'transaction_count': len(group),
                'avg_amount': round(group['amount'].mean(), 2) if len(group) > 0 else 0.0,
                'percentage': round((total_spent / total) * 100, 1) if total > 0 else 0.0
            }
        return summary

    def retrain_on_review(self, labeled_review_csv: str, base_csv: Optional[str] = None):
        """
        Optional helper: retrain model by combining existing training CSV and labeled review corrections.
        Expects labeled_review_csv with columns: description, amount, category
        """
        if not os.path.exists(labeled_review_csv):
            print("No labeled review file found.")
            return
        df_review = pd.read_csv(labeled_review_csv)
        if base_csv and os.path.exists(base_csv):
            df_base = pd.read_csv(base_csv)
            df_combined = pd.concat([df_base, df_review], ignore_index=True)
        else:
            df_combined = df_review
        print(f"Retraining on {len(df_combined)} combined samples...")
        self.train_ml_model(df_combined)
        self.save_model()
        print("Retraining complete and model saved.")

# --------------------------
# Quick CLI-style train/test demo when run directly
# --------------------------
def train_and_demo(csv_path: str = 'expenses_dataset.csv', model_path: str = MODEL_FILE_DEFAULT):
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"{csv_path} not found.")
    df = pd.read_csv(csv_path)
    c = ExpenseClassifierImproved()
    metrics = c.train_ml_model(df)
    print("Metrics:", metrics)
    results = c.classify_batch(df)
    print("Overall accuracy (on training set):", results.get('correct', pd.Series([False])).mean() if 'correct' in results.columns else None)
    c.save_model(model_path)
    return c, results

if __name__ == "__main__":
    # quick run
    classifier, results = train_and_demo(csv_path='expenses_dataset.csv')
    # print sample
    print(results.head(10).to_string(index=False))
