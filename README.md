# NeuroLens AI

This project is a premium `FastAPI + React` platform for Alzheimer's detection and clinical management:

- **User Authentication**: Secure Signup/Login for clinicians using JWT.
- **MRI Analysis**: Upload scans and classify into four Alzheimer-related stages.
- **Explainability**: Generate Grad-CAM heatmaps and LIME superpixel explanations.
- **Patient History**: Secure, user-isolated records stored in SQLite.
- **Professional Reports**: Export visual analysis and predictions as PDF documents.

## Project Structure

- `backend/`: FastAPI API, Auth logic, and Report generation.
- `frontend/`: React + Vite client (Refactored with React Router).
- `model/`: Inference utilities and ResNet18 model weights.

## Database

The backend now uses `SQLite` for persistence.

- Database file: `backend/data/neurolens.db`
- Stored data:
  - User credentials (hashed)
  - Analysis results (linked to User ID)
  - Uploaded image bytes
  - Prediction confidence and metadata

Each time you run `Run Analysis`, a new analysis record is saved automatically.
You can reopen saved analyses from the History view in the React UI.

## Backend Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m uvicorn app.main:app --reload
```

The API runs on `http://127.0.0.1:8000`. Documentation is available at `/docs`.

Keep this backend terminal running while you use the React app.

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The React app runs on `http://127.0.0.1:5173`.

If you want the frontend to call a different backend URL, set:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

in a `frontend/.env` file or export it before `npm run dev`.

## Deployment

Recommended setup:

- `frontend/` on `Vercel`
- `backend/` on `Render`

### 1. Deploy Backend on Render

This repo includes a root-level [`render.yaml`](/home/pavani_pothuganti/Desktop/Major%20Project/render.yaml) for the FastAPI backend.

Render configuration used:

- Build command: `pip install -r backend/requirements.txt`
- Start command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Persistent disk path: `/var/data/neurolens.db`

Environment variables to set in Render:

- `JWT_SECRET_KEY`: generated automatically by `render.yaml`
- `CORS_ORIGINS`: set this to your frontend URL after Vercel deploys
  Example:
  `https://your-frontend-name.vercel.app`
- `NEUROLENS_DB_PATH`: already set in `render.yaml` as `/var/data/neurolens.db`

Backend deployment steps:

1. Push this project to GitHub.
2. Go to Render.
3. Create a new Blueprint deployment from the GitHub repo.
4. Render will read `render.yaml` and create the FastAPI service.
5. After deployment, copy the backend public URL.

### 2. Deploy Frontend on Vercel

This repo includes [`frontend/vercel.json`](/home/pavani_pothuganti/Desktop/Major%20Project/frontend/vercel.json) for Vite build output and React Router rewrites.

Frontend deployment steps:

1. Import the GitHub repo into Vercel.
2. Set the project root directory to `frontend`.
3. Add environment variable:

```bash
VITE_API_BASE_URL=https://your-render-backend-url.onrender.com
```

4. Deploy the frontend.
5. Copy the Vercel URL.

### 3. Connect Frontend and Backend

After Vercel gives you the frontend URL:

1. Go back to Render.
2. Update `CORS_ORIGINS` with the Vercel app URL.
3. Redeploy the Render backend if needed.

### 4. Important Notes

- The backend uses `SQLite`, so the Render persistent disk is required.
- If the backend is redeployed without a disk, saved users and analysis history will be lost.
- For stronger production deployment later, you can migrate from SQLite to PostgreSQL.
- The first backend deploy may take longer because `torch` and related ML packages are large.

## API Endpoints

- `POST /api/auth/signup`: Create a new clinician account
- `POST /api/auth/login`: Authenticate and receive a JWT token
- `POST /api/predict`: Analyze an MRI scan (Requires Auth)
- `POST /api/explanations/gradcam`: Generate visual heatmap
- `GET /api/analyses`: View your personal analysis history
- `POST /api/reports/pdf`: Generate a clinical PDF report

All POST endpoints expect a multipart form upload with the `file` field.

## Notes

- The original Streamlit app is still present in `model/app.py` for reference.
- The model weights remain unchanged in `model/model/alzheimer_resnet18.pth`.
- The React frontend can call FastAPI directly through `VITE_API_BASE_URL`, so it does not depend on the Vite proxy being active.
