from fastapi import FastAPI, HTTPException, Depends, WebSocket, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt, JWTError
from reportlab.pdfgen import canvas
import os, csv, io

# CONFIG
DATABASE_URL = "sqlite:///./supermarket.db"
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# DATABASE
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Product(Base):
    __tablename__ = "products"
    id = Column(String, primary_key=True)
    name = Column(String)
    category = Column(String)
    stock = Column(Integer)
    price = Column(Float)
    barcode = Column(String, unique=True, index=True)

class Sale(Base):
    __tablename__ = "sales"
    id = Column(Integer, primary_key=True)
    product_id = Column(String)
    product_name = Column(String)
    quantity = Column(Integer)
    total = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    password = Column(String)

# THIS LINE MUST BE AFTER THE USER CLASS
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# --- HTML SERVING ROUTES ---
@app.get("/", response_class=HTMLResponse)
async def read_pos():
    with open("pos.html") as f: return f.read()

@app.get("/admin", response_class=HTMLResponse)
async def read_admin():
    with open("admin.html") as f: return f.read()

@app.get("/sales", response_class=HTMLResponse)
async def read_sales():
    with open("sales.html") as f: return f.read()

# --- API ROUTES ---
@app.get("/api/inventory")
def get_inventory(db: Session = Depends(get_db)):
    return db.query(Product).all()

@app.get("/api/barcode/{barcode}")
def search_barcode(barcode: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.barcode == barcode.strip()).first()
    if not product: raise HTTPException(status_code=404)
    return product

@app.post("/api/products/upload")
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    stream = io.StringIO(content.decode('utf-8'))
    reader = csv.DictReader(stream)
    for row in reader:
        barcode = row['barcode'].strip()
        prod = db.query(Product).filter(Product.barcode == barcode).first()
        if prod:
            prod.name, prod.price, prod.stock = row['name'], float(row['price']), int(row['stock'])
        else:
            db.add(Product(id=row['id'], name=row['name'], category=row['category'], stock=int(row['stock']), price=float(row['price']), barcode=barcode))
    db.commit()
    return {"message": "Import Successful"}

@app.get("/api/sales/history")
def get_sales(db: Session = Depends(get_db)):
    return db.query(Sale).order_by(Sale.created_at.desc()).all()

@app.get("/api/analytics/revenue")
def total_revenue(db: Session = Depends(get_db)):
    sales = db.query(Sale).all()
    return {"total_revenue": sum(s.total for s in sales)}

@app.delete("/api/products/clear")
def clear_inventory(db: Session = Depends(get_db)):
    db.query(Product).delete()
    db.commit()
    return {"message": "Inventory Cleared"}
# Add this to your imports at the top
from pydantic import BaseModel

# Add this Schema
class UserSchema(BaseModel):
    username: str
    password: str

# Add these two routes
@app.post("/register")
def register(user: UserSchema, db: Session = Depends(get_db)):
    # For now, we store plain text for the fast test
    # In a real app, use the pwd_context we discussed earlier
    new_user = User(username=user.username, password=user.password)
    db.add(new_user)
    db.commit()
    return {"message": "User created!"}

@app.post("/login")
def login(user: UserSchema, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or db_user.password != user.password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    return {"message": "Login successful", "access_token": "fake-proto-token"}


from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
def read_root():
    try:
        with open("pos.html", "r") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>pos.html not found! Check if you uploaded it to GitHub.</h1>"

@app.get("/admin", response_class=HTMLResponse)
def read_admin():
    try:
        with open("admin.html", "r") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>admin.html not found!</h1>"