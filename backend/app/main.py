import os

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from .auth_utils import (
    get_current_user,
    get_password_hash,
    verify_password,
    create_access_token,
)
from .database import get_connection, init_db, save_analysis, get_analysis
from .history import get_analysis_detail, get_recent_analyses
from .reports import generate_report_pdf
from .schemas import (
    AnalysisDetail,
    AnalysisRecord,
    ExplanationResponse,
    HealthResponse,
    PredictionResponse,
    ReportRequest,
    UserCreate,
    Token,
)
from .services import (
    build_gradcam_explanation,
    build_lime_explanation,
    build_prediction_payload,
    read_image,
)


app = FastAPI(title="NeuroLens AI API", version="1.0.0")

cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
)
allowed_origins = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/api/health", response_model=HealthResponse)
def health_check():
    return {"status": "ok"}


# AUTH ENDPOINTS

@app.post("/api/auth/signup", response_model=Token)
async def signup(user: UserCreate):
    with get_connection() as conn:
        existing_user = conn.execute("SELECT id FROM users WHERE username = ? OR email = ?", (user.username, user.email)).fetchone()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username or email already exists")
        
        hashed_password = get_password_hash(user.password)
        cursor = conn.execute(
            "INSERT INTO users (username, email, hashed_password) VALUES (?, ?, ?)",
            (user.username, user.email, hashed_password)
        )
        conn.commit()
        user_id = cursor.lastrowid
        
    user_data = {"id": user_id, "username": user.username, "email": user.email}
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "user": user_data}

@app.post("/api/auth/login", response_model=Token)
async def login(user_credentials: UserCreate):
    with get_connection() as conn:
        user = conn.execute("SELECT id, username, email, hashed_password FROM users WHERE username = ?", (user_credentials.username,)).fetchone()
        if not user or not verify_password(user_credentials.password, user["hashed_password"]):
            raise HTTPException(status_code=401, detail="Invalid username or password")
    
    user_data = {"id": user["id"], "username": user["username"], "email": user["email"]}
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "user": user_data}


# PROTECTED ANALYSIS ENDPOINTS

@app.post("/api/predict", response_model=PredictionResponse)
async def predict(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload a valid image file.")

    file_bytes = await file.read()
    image = read_image(file_bytes)
    prediction_payload = build_prediction_payload(image)
    analysis_id = save_analysis(
        user_id=current_user["id"],
        file_name=file.filename or "uploaded-image",
        content_type=file.content_type,
        file_bytes=file_bytes,
        prediction_payload=prediction_payload,
    )
    return {"analysis_id": analysis_id, **prediction_payload}


@app.post("/api/explanations/gradcam", response_model=ExplanationResponse)
async def gradcam_explanation(
    file: UploadFile = File(...),
    overlay_opacity: float = Query(0.5, ge=0.1, le=0.9),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload a valid image file.")

    image = read_image(await file.read())
    image_base64 = build_gradcam_explanation(image, overlay_opacity)
    return {"method": "gradcam", "image_base64": image_base64}


@app.post("/api/explanations/lime", response_model=ExplanationResponse)
async def lime_explanation(
    file: UploadFile = File(...),
    num_samples: int = Query(1000, ge=200, le=1500),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload a valid image file.")

    image = read_image(await file.read())
    image_base64 = build_lime_explanation(image, num_samples)
    return {"method": "lime", "image_base64": image_base64}


@app.get("/api/analyses", response_model=list[AnalysisRecord])
def list_analysis_history(
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user)
):
    return get_recent_analyses(user_id=current_user["id"], limit=limit)


@app.get("/api/analyses/{analysis_id}", response_model=AnalysisDetail)
def analysis_detail(
    analysis_id: int,
    current_user: dict = Depends(get_current_user)
):
    analysis = get_analysis_detail(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    
    # Ownership Check
    # Analysis row contains user_id. We need to check it.
    actual_analysis = get_analysis(analysis_id)
    if actual_analysis["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to view this analysis.")
        
    return analysis


@app.post("/api/reports/pdf")
async def report_pdf(
    request: ReportRequest,
    current_user: dict = Depends(get_current_user)
):
    analysis = get_analysis(request.analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    if analysis["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this report.")

    pdf_bytes = generate_report_pdf(
        analysis,
        gradcam_base64=request.gradcam_base64,
        lime_base64=request.lime_base64,
    )

    return Response(
        content=bytes(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=neurolens_report_{request.analysis_id}.pdf"
        },
    )
