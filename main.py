from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from database import engine, Base, get_db
from models import User, Transaction
from auth import hash_password, verify_password, create_access_token, get_current_user
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.sql import func

app = FastAPI()

Base.metadata.create_all(bind=engine)

# Register a new user
@app.post("/register/")
def register(username: str, email: str, password: str, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_pwd = hash_password(password)
    new_user = User(username=username, email=email, hashed_password=hashed_pwd)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully"}

# Login to get JWT token
@app.post("/login/")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# Add a transaction
@app.post("/transactions/")
def add_transaction(amount: float, category: str, description: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    transaction = Transaction(amount=amount, category=category, description=description, user_id=user.id)
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction

# Get transactions with filters & pagination
@app.get("/transactions/")
def get_transactions(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    category: str = None,
    start_date: str = None,
    end_date: str = None,
    page: int = Query(1, alias="page", ge=1),
    limit: int = Query(10, alias="limit", ge=1, le=100)
):
    query = db.query(Transaction).filter(Transaction.user_id == user.id)

    if category:
        query = query.filter(Transaction.category == category)
    if start_date:
        query = query.filter(Transaction.date >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(Transaction.date <= datetime.fromisoformat(end_date))

    total = query.count()
    transactions = query.offset((page - 1) * limit).limit(limit).all()

    return {"total": total, "page": page, "limit": limit, "transactions": transactions}

# Monthly spending insights
@app.get("/analytics/monthly/")
def get_monthly_spending(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    monthly_data = (
        db.query(
            func.date_trunc('month', Transaction.date).label("month"),
            func.sum(Transaction.amount).label("total_spent")
        )
        .filter(Transaction.user_id == user.id)
        .group_by("month")
        .order_by("month")
        .all()
    )

    return [{"month": str(data.month), "total_spent": float(data.total_spent)} for data in monthly_data]
