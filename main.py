from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import odin_backend

app = FastAPI()

# ✅ Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to ["http://localhost:5173"] in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "ODIN Backend API is online! 🚀"}

@app.post("/api/plan_trajectory")
def plan_trajectory():
    try:
        decision_data = odin_backend.run_full_pipeline()
        return {
            "status": "success",
            "message": "Trajectory planning completed successfully.",
            "decision": decision_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
