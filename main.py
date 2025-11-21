import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from bson.objectid import ObjectId

from database import db, create_document, get_documents

app = FastAPI(title="AlumniConnect API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Models for requests
# -------------------------
class SignupPayload(BaseModel):
    name: str
    email: str
    status: str  # 'alumnus' | 'student'
    phone: Optional[str] = None
    batch_year: Optional[int] = None
    department: Optional[str] = None
    current_company: Optional[str] = None
    designation: Optional[str] = None

class LoginPayload(BaseModel):
    email: str

class ProfileUpdatePayload(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    batch_year: Optional[int] = None
    department: Optional[str] = None
    current_company: Optional[str] = None
    designation: Optional[str] = None
    status: Optional[str] = None

# -------------------------
# Helpers
# -------------------------

def to_public(doc: dict):
    if not doc:
        return None
    d = doc.copy()
    if "_id" in d:
        d["id"] = str(d.pop("_id"))
    return d

# -------------------------
# Core Endpoints
# -------------------------
@app.get("/")
def read_root():
    return {"message": "AlumniConnect API running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response

# Mock auth: sign up creates or updates a user and returns a fake token = email
@app.post("/auth/signup")
def signup(payload: SignupPayload):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    user_col = db["user"]
    existing = user_col.find_one({"email": payload.email})
    data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if existing:
        user_col.update_one({"_id": existing["_id"]}, {"$set": data})
        doc = user_col.find_one({"_id": existing["_id"]})
    else:
        _id = user_col.insert_one(data).inserted_id
        doc = user_col.find_one({"_id": _id})
    return {"token": payload.email, "user": to_public(doc)}

# Mock auth: login by email only
@app.post("/auth/login")
def login(payload: LoginPayload):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    user_col = db["user"]
    doc = user_col.find_one({"email": payload.email})
    if not doc:
        # Auto-provision minimal student/alumnus with unknowns
        _id = user_col.insert_one({"email": payload.email, "status": "student", "name": payload.email.split("@")[0]}).inserted_id
        doc = user_col.find_one({"_id": _id})
    return {"token": payload.email, "user": to_public(doc)}

# Get current profile by email used as token (mock)
@app.get("/users/profile")
def get_profile(email: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    user_col = db["user"]
    doc = user_col.find_one({"email": email})
    if not doc:
        raise HTTPException(status_code=404, detail="User not found")
    return to_public(doc)

# Update profile fields by email
@app.put("/users/profile")
def update_profile(email: str, payload: ProfileUpdatePayload = ...):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    user_col = db["user"]
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    res = user_col.update_one({"email": email}, {"$set": updates})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    doc = user_col.find_one({"email": email})
    return to_public(doc)

# Directory search by company or batch year
@app.get("/directory")
def directory(company: Optional[str] = None, batch_year: Optional[int] = None, limit: int = 50):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    filt = {}
    if company:
        filt["current_company"] = {"$regex": company, "$options": "i"}
    if batch_year is not None:
        filt["batch_year"] = batch_year
    docs = db["user"].find(filt).limit(limit)
    return [to_public(d) for d in docs]

# Events list (basic, can insert a sample if none exists)
@app.get("/events")
def events():
    if db is None:
        # Return a sample list even if DB missing to keep demo running
        return [{"title": "Annual Alumni Meet", "date": "2025-02-15", "description": "Reconnect with your batch and faculty", "audience": "All"}]
    col = db["event"]
    existing = list(col.find({}).limit(10))
    if not existing:
        col.insert_one({"title": "Annual Alumni Meet", "date": "2025-02-15", "description": "Reconnect with your batch and faculty", "audience": "All"})
        existing = list(col.find({}).limit(10))
    return [to_public(e) for e in existing]

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
