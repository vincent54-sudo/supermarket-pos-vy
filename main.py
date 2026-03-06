from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from datetime import datetime
from contextlib import asynccontextmanager
import os, csv, io

# --- DATABASE SETUP ---
DATABASE_URL = "sqlite:///./supermarket.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Product(Base):
    __tablename__ = "products"
    id = Column(String, primary_key=True)
    name = Column(String); category = Column(String)
    stock = Column(Integer); price = Column(Float); barcode = Column(String, unique=True, index=True)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True); password = Column(String)

# Create tables immediately
Base.metadata.create_all(bind=engine)

# --- STARTUP LOGIC (New Modern Way) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # This runs when the server starts
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "NETHUNTER").first()
        if not admin:
            db.add(User(username="NETHUNTER", password="Exothamic004."))
            db.commit()
    finally:
        db.close()
    yield
    # Code here runs when the server shuts down

app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class UserSchema(BaseModel):
    username: str
    password: str

# --- ROUTES ---

@app.post("/login")
def login(user: UserSchema, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or db_user.password != user.password:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return {"message": "Login successful", "access_token": "token123"}

@app.get("/api/barcode/{barcode}")
def search_barcode(barcode: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.barcode == barcode.strip()).first()
    if not product:
        raise HTTPException(status_code=404, detail="Not Found")
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
            prod.name, prod.price = row['name'], float(row['price'])
        else:
            db.add(Product(id=row['id'], name=row['name'], category=row['category'], 
                         stock=int(row['stock']), price=float(row['price']), barcode=barcode))
    db.commit()
    return {"message": "Success"}

@app.get("/", response_class=HTMLResponse)
async def read_root():
    fname = "index.html" if os.path.exists("index.html") else "pos.html"
    if os.path.exists(fname):
        with open(fname, "r") as f: return f.read()
    return "<h1>No HTML file found!</h1>"

@app.get("/login", response_class=HTMLResponse)
async def get_login_page():
    if os.path.exists("login.html"):
        with open("login.html", "r") as f: return f.read()
    return "<h1>login.html not found!</h1>"

app.mount("/", StaticFiles(directory="."), name="static")