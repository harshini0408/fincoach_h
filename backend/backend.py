from fastapi import FastAPI, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from expense_classifier import ExpenseClassifier
from anomaly_detector import SpendingAnomalyDetector
from ai_financial_advisor import FinancialAdvisor
from chatbot_coach import ChatbotCoach

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, set allowed frontend URL(s)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

classifier = ExpenseClassifier()
anomaly_detector = SpendingAnomalyDetector()
advisor = FinancialAdvisor()
chatbot = ChatbotCoach()

@app.post("/classify-expenses/")
async def classify_expenses(file: UploadFile = File(...)):
    df = pd.read_csv(file.file)
    classified_df = classifier.classify_batch(df)
    return classified_df.to_dict(orient="records")

@app.post("/detect-anomalies/")
async def detect_anomalies(file: UploadFile = File(...)):
    df = pd.read_csv(file.file)
    anomalies = anomaly_detector.generate_anomaly_report(df)
    return anomalies

@app.post("/financial-advice/")
async def financial_advice(file: UploadFile = File(...)):
    df = pd.read_csv(file.file)
    advice = advisor.create_comprehensive_report(df)
    return advice

@app.post("/chatbot/")
async def chat_with_ai(request: Request):
    body = await request.json()
    message = body.get("message", "")
    response = chatbot.chat(message)
    return {"response": response}

