from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from datetime import datetime
import os, csv, io

DATABASE_URL = "sqlite:///./supermarket.db"
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

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

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

class UserSchema(BaseModel):
    username: str; password: str

@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    # Check if admin exists, if not, create it
    admin = db.query(User).filter(User.username == "NETHUNTER").first()
    if not admin:
        new_user = User(username="admin", password="Exothamic004.") # Change these!
        db.add(new_user)
        db.commit()
    db.close()

# --- AUTH ROUTES ---
@app.post("/login")
def login(user: UserSchema, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or db_user.password != user.password:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return {"message": "Login successful", "access_token": "fake-token-123"}

# --- HTML ROUTES ---
@app.get("/", response_class=HTMLResponse)
async def read_root():
    # If the user isn't logged in, the HTML script usually handles redirect to login.html
    for fname in ["index.html", "pos.html"]:
        if os.path.exists(fname):
            with open(fname, "r") as f: return f.read()
    return "<h1>POS File Not Found</h1>"

@app.get("/login", response_class=HTMLResponse)
async def get_login_page():
    with open("login.html", "r") as f: return f.read()

# --- API ROUTES ---
@app.get("/api/barcode/{barcode}")
def search_barcode(barcode: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.barcode == barcode.strip()).first()
    if not product: raise HTTPException(status_code=404)
    return product

app.mount("/", StaticFiles(directory="."), name="static")