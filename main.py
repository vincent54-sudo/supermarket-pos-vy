from fastapi import FastAPI, HTTPException, Depends, WebSocket, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from datetime import datetime
import os, csv, io

# CONFIG
DATABASE_URL = "sqlite:///./supermarket.db"
app = FastAPI()

# Enable CORS
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# DATABASE SETUP
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

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    password = Column(String)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# --- HTML ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def read_root():
    # Try to open your Scanner page first
    for filename in ["pos.html", "index.html"]:
        if os.path.exists(filename):
            with open(filename, "r") as f:
                return f.read()
    return "<h1>No HTML files found! Please check your GitHub files.</h1>"

@app.get("/admin", response_class=HTMLResponse)
async def read_admin_page():
    if os.path.exists("admin.html"):
        with open("admin.html", "r") as f:
            return f.read()
    return "<h1>admin.html not found!</h1>"

@app.get("/dashboard", response_class=HTMLResponse)
async def read_dashboard_page():
    if os.path.exists("dashboard.html"):
        with open("dashboard.html", "r") as f:
            return f.read()
    return "<h1>dashboard.html not found!</h1>"

# --- API ROUTES ---

@app.get("/api/inventory")
def get_inventory(db: Session = Depends(get_db)):
    return db.query(Product).all()

@app.get("/api/barcode/{barcode}")
def search_barcode(barcode: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.barcode == barcode.strip()).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
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
            prod.name = row['name']
            prod.price = float(row['price'])
            prod.stock = int(row['stock'])
        else:
            db.add(Product(id=row['id'], name=row['name'], category=row['category'], stock=int(row['stock']), price=float(row['price']), barcode=barcode))
    db.commit()
    return {"message": "Import Successful"}

# --- STATIC FILES SUPPORT ---
app.mount("/", StaticFiles(directory="."), name="static")