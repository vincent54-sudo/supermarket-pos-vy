from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from contextlib import asynccontextmanager
import os, csv, io, re

# --- DATABASE SETUP ---
DATABASE_URL = "sqlite:///./supermarket.db"
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

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    password = Column(String)

# Create tables immediately on script load
Base.metadata.create_all(bind=engine)

# --- STARTUP LOGIC ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # This creates your specific credentials automatically on startup
    db = SessionLocal()
    try:
        admin_user = "NETHUNTER"
        admin_pass = "Exothamic004."
        admin = db.query(User).filter(User.username == admin_user).first()
        if not admin:
            db.add(User(username=admin_user, password=admin_pass))
            db.commit()
        else:
            # Ensure password is updated if you changed it in the code
            admin.password = admin_pass
            db.commit()
    finally:
        db.close()
    yield

app = FastAPI(lifespan=lifespan)

# CORS middleware to allow your frontend to talk to the backend
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_methods=["*"], 
    allow_headers=["*"]
)

# Dependency to get database session
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
    # 1. Remove any non-numeric characters (spaces, newlines, etc.)
    clean_code = re.sub(r'\D', '', barcode)
    
    # 2. Search for the exact code
    product = db.query(Product).filter(Product.barcode == clean_code).first()
    
    # 3. If not found, try searching without leading zeros
    if not product:
        product = db.query(Product).filter(Product.barcode == clean_code.lstrip('0')).first()

    if not product:
        raise HTTPException(status_code=404, detail=f"Product {clean_code} not found")
    return product

@app.post("/api/products/upload")
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        content = await file.read()
        # 'utf-8-sig' handles Excel-specific hidden characters
        stream = io.StringIO(content.decode('utf-8-sig'))
        reader = csv.DictReader(stream)
        
        rows_added = 0
        for row in reader:
            # Standardize headers: lowercase and no spaces
            row = {k.strip().lower(): v.strip() for k, v in row.items() if k}
            
            barcode_val = row.get('barcode')
            if not barcode_val:
                continue

            # Upsert logic: Update if exists, create if new
            prod = db.query(Product).filter(Product.barcode == barcode_val).first()
            
            # Clean numeric data
            price_val = float(row.get('price', 0).replace('$', '').replace(',', ''))
            stock_val = int(row.get('stock', 0))

            if prod:
                prod.name = row.get('name', prod.name)
                prod.price = price_val
                prod.stock = stock_val
                prod.category = row.get('category', prod.category)
            else:
                db.add(Product(
                    id=row.get('id', barcode_val),
                    name=row.get('name', 'N/A'),
                    category=row.get('category', 'General'),
                    stock=stock_val,
                    price=price_val,
                    barcode=barcode_val
                ))
            rows_added += 1
            
        db.commit()
        return {"message": f"Successfully processed {rows_added} products"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV Error: {str(e)}")

# --- HTML SERVING ---

@app.get("/", response_class=HTMLResponse)
async def read_root():
    # Priority order for loading your main app page
    for page in ["index.html", "pos.html"]:
        if os.path.exists(page):
            with open(page, "r") as f: return f.read()
    return "<h1>Scanner Page (index.html) not found!</h1>"

@app.get("/login", response_class=HTMLResponse)
async def get_login_page():
    if os.path.exists("login.html"):
        with open("login.html", "r") as f: return f.read()
    return "<h1>login.html not found!</h1>"

# Mount static files last
app.mount("/", StaticFiles(directory="."), name="static")