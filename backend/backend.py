from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
import pandas as pd
import io
from datetime import datetime
from typing import Optional, Dict, Any
import os

# Import database and models
from database import init_db, get_db, SessionLocal
from models import User, Transaction, SavingsGoal, ChatMessage, Category

# Import AI modules
from expense_classifier import ExpenseClassifier
from anomaly_detector import SpendingAnomalyDetector
from ai_financial_advisor import FinancialAdvisor
from chatbot_coach import ChatbotCoach

# Initialize FastAPI app
app = FastAPI(title="FinCoach API", version="2.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI modules
classifier = ExpenseClassifier()
anomaly_detector = SpendingAnomalyDetector()
advisor = FinancialAdvisor()
chatbot = ChatbotCoach()

# Load classifier model if exists
if os.path.exists('expense_classifier_model.pkl'):
    try:
        classifier.load_model('expense_classifier_model.pkl')
        print("✅ Loaded expense classifier model")
    except Exception as e:
        print(f"⚠ Could not load classifier model: {e}")

# ========== PYDANTIC MODELS ==========
class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    email: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class ExpenseCreate(BaseModel):
    transaction_date: str
    description: str
    amount: float
    category_id: Optional[str] = None
class GoalCreate(BaseModel):
    name: str
    monthly_target: float
    deadline: Optional[str] = None

class GoalUpdate(BaseModel):
    monthly_target: Optional[float] = None
    active: Optional[bool] = None

class ChatRequest(BaseModel):
    message: str
    context: Dict[str, Any] = {}

# ========== HELPER FUNCTIONS ==========
def hash_password(password: str) -> str:
    """Simple password hashing (use bcrypt in production)"""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def get_category_id_from_name(category_name: str, db: Session) -> str:
    """Map category name to category ID"""
    category = db.query(Category).filter(Category.name == category_name).first()
    if category:
        return str(category.id)
    return "6"  # Default to "Others"

# ========== STARTUP EVENT ==========
@app.on_event("startup")
async def startup_event():
    """Initialize database and add default categories"""
    try:
        init_db()
        
        # Add default categories
        db = SessionLocal()
        try:
            if db.query(Category).count() == 0:
                default_categories = [
                    Category(id=1, name='Food', icon='🍔', color='#ef4444'),
                    Category(id=2, name='Travel', icon='🚗', color='#3b82f6'),
                    Category(id=3, name='Shopping', icon='🛍️', color='#f59e0b'),
                    Category(id=4, name='Bills', icon='💡', color='#10b981'),
                    Category(id=5, name='Subscriptions', icon='📱', color='#8b5cf6'),
                    Category(id=6, name='Others', icon='📦', color='#6b7280'),
                ]
                db.add_all(default_categories)
                db.commit()
                print("✅ Default categories added")
        except Exception as e:
            print(f"Categories might already exist: {e}")
        finally:
            db.close()
    except Exception as e:
        print(f"⚠ Startup error: {e}")

# ========== API ENDPOINTS ==========

@app.get("/")
def root():
    return {
        "message": "FinCoach API",
        "status": "healthy",
        "version": "2.0.0",
        "endpoints": {
            "health": "/health",
            "auth": "/api/auth/signup, /api/auth/login",
            "expenses": "/api/expenses/{user_id}",
            "goals": "/api/goals/{user_id}",
            "chatbot": "/api/chatbot/{user_id}",
            "dashboard": "/api/dashboard/{user_id}"
        }
    }

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

# ========== AUTHENTICATION ==========

@app.post("/api/auth/signup")
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register new user"""
    try:
        # Check if username exists
        existing = db.query(User).filter(User.username == user_data.username).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Create user
        new_user = User(
            username=user_data.username,
            password_hash=hash_password(user_data.password),
            full_name=user_data.full_name,
            email=user_data.email
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return {
            "success": True,
            "user": {
                "id": str(new_user.id),
                "username": new_user.username,
                "full_name": new_user.full_name
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/login")
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user"""
    try:
        user = db.query(User).filter(
            User.username == credentials.username,
            User.password_hash == hash_password(credentials.password)
        ).first()
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        return {
            "success": True,
            "user": {
                "id": str(user.id),
                "username": user.username,
                "full_name": user.full_name
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========== CATEGORIES ==========

@app.get("/api/categories")
def get_categories(db: Session = Depends(get_db)):
    """Get all categories"""
    categories = db.query(Category).all()
    return {
        "categories": [
            {
                "id": str(cat.id),
                "name": cat.name,
                "icon": cat.icon,
                "color": cat.color
            }
            for cat in categories
        ]
    }

# ========== EXPENSES ==========

@app.get("/api/expenses/{user_id}")
def get_user_expenses(user_id: str, db: Session = Depends(get_db)):
    """Get all expenses for a user"""
    try:
        transactions = db.query(Transaction).filter(
            Transaction.user_id == int(user_id)
        ).order_by(Transaction.transaction_date.desc()).all()
        
        return {
            "expenses": [
                {
                    "id": str(t.id),
                    "userId": str(t.user_id),
                    "transactionDate": t.transaction_date.isoformat(),
                    "description": t.description,
                    "amount": t.amount,
                    "categoryId": t.category_id or "6",
                    "predicted_category": t.predicted_category,
                    "confidence": t.confidence
                }
                for t in transactions
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/expenses/{user_id}")
def add_expense(user_id: str, expense: ExpenseCreate, db: Session = Depends(get_db)):
    """Add single expense"""
    try:
        # Classify the expense
        prediction = classifier.predict_single(expense.description, expense.amount)
        category_id = get_category_id_from_name(prediction['category'], db)
        
        # Parse date
        try:
            transaction_date = datetime.fromisoformat(expense.transaction_date.replace('Z', '+00:00'))
        except:
            transaction_date = datetime.now()
        
        transaction = Transaction(
            user_id=int(user_id),
            transaction_date=transaction_date,
            description=expense.description,
            amount=expense.amount,
            category_id=expense.category_id,
            predicted_category=prediction['category'],
            confidence=prediction['confidence'],
            method=prediction['method']
        )
        
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        print(f"✅ Added expense: {transaction.description} - ₹{transaction.amount}")
        
        return {
            "success": True,
            "expense": {
                "id": str(transaction.id),
                "userId": str(transaction.user_id),
                "transactionDate": transaction.transaction_date.isoformat(),
                "description": transaction.description,
                "amount": transaction.amount,
                "categoryId": transaction.category_id,
                "predicted_category": transaction.predicted_category,
                "confidence": transaction.confidence
            }
        }
    except Exception as e:
        db.rollback()
        print(f"❌ Error adding expense: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/expenses/{user_id}/upload")
async def upload_expenses(user_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload CSV file with expenses"""
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        # Classify expenses
        classified_df = classifier.classify_batch(df)
        
        # Save to database
        saved_count = 0
        for _, row in classified_df.iterrows():
            try:
                transaction_date = pd.to_datetime(row['date'])
                category_id = get_category_id_from_name(row['predicted_category'], db)
                
                transaction = Transaction(
                    user_id=int(user_id),
                    transaction_date=transaction_date,
                    description=str(row['description']),
                    amount=float(row['amount']),
                    category_id=category_id,
                    predicted_category=row['predicted_category'],
                    confidence=float(row.get('confidence', 0.0)),
                    method=row.get('method', 'ml')
                )
                
                db.add(transaction)
                saved_count += 1
            except Exception as row_error:
                print(f"Error processing row: {row_error}")
                continue
        
        db.commit()
        print(f"✅ Saved {saved_count} transactions to database")
        
        return {
            "success": True,
            "message": f"Successfully uploaded {saved_count} transactions",
            "count": saved_count
        }
    except Exception as e:
        db.rollback()
        print(f"❌ Error uploading expenses: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/expenses/{expense_id}")
def delete_expense(expense_id: str, db: Session = Depends(get_db)):
    """Delete an expense"""
    try:
        transaction = db.query(Transaction).filter(Transaction.id == int(expense_id)).first()
        if not transaction:
            raise HTTPException(status_code=404, detail="Expense not found")
        
        db.delete(transaction)
        db.commit()
        
        return {"success": True, "message": "Expense deleted"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ========== GOALS ==========

@app.get("/api/goals/{user_id}")
def get_user_goals(user_id: str, db: Session = Depends(get_db)):
    """Get all goals for a user"""
    try:
        goals = db.query(SavingsGoal).filter(
            SavingsGoal.user_id == int(user_id)
        ).all()
        
        return {
            "goals": [
                {
                    "id": str(g.id),
                    "userId": str(g.user_id),
                    "name": g.name,
                    "monthlyTarget": g.monthly_target,
                    "currentAmount": g.current_amount,
                    "deadline": g.deadline.isoformat() if g.deadline else None,
                    "active": g.active
                }
                for g in goals
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/goals/{user_id}")
def create_goal(user_id: str, goal: GoalCreate, db: Session = Depends(get_db)):
    """Create a new goal"""
    try:
        # Deactivate other goals
        db.query(SavingsGoal).filter(SavingsGoal.user_id == int(user_id)).update({"active": False})
        
        deadline = None
        if goal.deadline:
            try:
                deadline = datetime.fromisoformat(goal.deadline.replace('Z', '+00:00'))
            except:
                pass
        
        new_goal = SavingsGoal(
            user_id=int(user_id),
            name=goal.name,
            monthly_target=goal.monthly_target,
            deadline=deadline,
            active=True
        )
        
        db.add(new_goal)
        db.commit()
        db.refresh(new_goal)
        
        return {
            "success": True,
            "goal": {
                "id": str(new_goal.id),
                "userId": str(new_goal.user_id),
                "name": new_goal.name,
                "monthlyTarget": new_goal.monthly_target,
                "active": new_goal.active
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/goals/{goal_id}")
def update_goal(goal_id: str, updates: GoalUpdate, db: Session = Depends(get_db)):
    """Update a goal"""
    try:
        goal = db.query(SavingsGoal).filter(SavingsGoal.id == int(goal_id)).first()
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
        
        if updates.monthly_target is not None:
            goal.monthly_target = updates.monthly_target
        if updates.active is not None:
            if updates.active:
                db.query(SavingsGoal).filter(
                    SavingsGoal.user_id == goal.user_id,
                    SavingsGoal.id != goal.id
                ).update({"active": False})
            goal.active = updates.active
        
        db.commit()
        db.refresh(goal)
        
        return {"success": True, "goal": {"id": str(goal.id), "active": goal.active}}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/goals/{goal_id}")
def delete_goal(goal_id: str, db: Session = Depends(get_db)):
    """Delete a goal"""
    try:
        goal = db.query(SavingsGoal).filter(SavingsGoal.id == int(goal_id)).first()
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
        
        db.delete(goal)
        db.commit()
        
        return {"success": True, "message": "Goal deleted"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ========== CHATBOT ==========

@app.post("/api/chatbot/{user_id}")
async def chat_endpoint(user_id: str, request: ChatRequest, db: Session = Depends(get_db)):
    """Chat with AI"""
    try:
        transactions = db.query(Transaction).filter(Transaction.user_id == int(user_id)).all()
        goals = db.query(SavingsGoal).filter(SavingsGoal.user_id == int(user_id), SavingsGoal.active == True).first()
        
        total_spending = sum(t.amount for t in transactions)
        context = {
            **request.context,
            "total_spending": total_spending,
            "transaction_count": len(transactions)
        }
        
        if goals:
            context["savings_goal"] = goals.monthly_target
        
        response = chatbot.chat(request.message, context=context)
        
        chat_message = ChatMessage(
            user_id=int(user_id),
            message=request.message,
            response=response
        )
        db.add(chat_message)
        db.commit()
        
        return {"response": response}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chatbot/{user_id}/history")
def get_chat_history(user_id: str, limit: int = 50, db: Session = Depends(get_db)):
    """Get chat history"""
    try:
        messages = db.query(ChatMessage).filter(
            ChatMessage.user_id == int(user_id)
        ).order_by(ChatMessage.created_at.desc()).limit(limit).all()
        
        return {
            "messages": [
                {
                    "id": str(m.id),
                    "userId": str(m.user_id),
                    "message": m.message,
                    "response": m.response,
                    "createdAt": m.created_at.isoformat()
                }
                for m in reversed(messages)
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========== DASHBOARD ==========

@app.get("/api/dashboard/{user_id}")
def get_dashboard(user_id: str, db: Session = Depends(get_db)):
    """Get dashboard data"""
    try:
        now = datetime.now()
        start_of_month = datetime(now.year, now.month, 1)
        
        transactions = db.query(Transaction).filter(
            Transaction.user_id == int(user_id),
            Transaction.transaction_date >= start_of_month
        ).all()
        
        if not transactions:
            return {
                "totalSpent": 0,
                "transactionCount": 0,
                "categoryBreakdown": [],
                "weeklyTrend": []
            }
        
        total_spent = sum(t.amount for t in transactions)
        
        category_totals = {}
        for t in transactions:
            cat = t.predicted_category or "Others"
            category_totals[cat] = category_totals.get(cat, 0) + t.amount
        
        category_breakdown = [
            {
                "category": cat,
                "amount": amt,
                "percentage": (amt / total_spent * 100) if total_spent > 0 else 0
            }
            for cat, amt in category_totals.items()
        ]
        
        return {
            "totalSpent": round(total_spent, 2),
            "transactionCount": len(transactions),
            "categoryBreakdown": category_breakdown,
            "weeklyTrend": []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========== LEGACY ENDPOINTS (for compatibility) ==========

@app.post("/add-expenses/")
async def legacy_add_expenses(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Legacy endpoint - use /api/expenses/{user_id}/upload instead"""
    return {"message": "Please use /api/expenses/{user_id}/upload endpoint"}

@app.get("/expenses/")
def legacy_get_expenses(db: Session = Depends(get_db)):
    """Legacy endpoint"""
    return {"message": "Please use /api/expenses/{user_id} endpoint"}

@app.post("/classify-expenses/")
async def classify_expenses(file: UploadFile = File(...)):
    """Classify expenses from CSV"""
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        classified_df = classifier.classify_batch(df)
        return classified_df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/detect-anomalies/")
async def detect_anomalies(file: UploadFile = File(...)):
    """Detect anomalies in expenses"""
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        anomalies = anomaly_detector.generate_anomaly_report(df)
        return anomalies
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/financial-advice/")
async def financial_advice(file: UploadFile = File(...)):
    """Get financial advice"""
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        advice = advisor.create_comprehensive_report(df)
        return advice
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Run server
if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting FinCoach API...")
    print("📊 Database:", os.getenv("DATABASE_URL", "postgresql://..."))
    uvicorn.run("backend:app", host="0.0.0.0", port=8000, reload=True)

