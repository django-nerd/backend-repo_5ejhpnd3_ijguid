import os
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4
from datetime import datetime

from database import db, create_document, get_documents
from schemas import VideoJob, WaitlistUser

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class WaitlistPayload(BaseModel):
    email: str
    name: Optional[str] = None
    source: Optional[str] = "marketing"


@app.get("/")
def read_root():
    return {"message": "synk.ai backend running"}


@app.post("/api/waitlist")
def waitlist_signup(payload: WaitlistPayload):
    try:
        doc_id = create_document("waitlistuser", payload.dict())
        return {"ok": True, "id": doc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


UPLOAD_DIR = "uploads"
OUTPUT_DIR = "renders"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


def fake_ai_processing(job_id: str, input_path: str):
    # Simulate AI pipeline by updating progress and generating a dummy output URL
    try:
        from time import sleep
        steps = [
            ("analyze_content", 15),
            ("detect_cuts", 30),
            ("auto_captions", 45),
            ("select_music", 60),
            ("insert_b_roll", 80),
            ("color_and_export", 100),
        ]
        for step, prog in steps:
            db["videojob"].update_one({"_id": db["videojob"].find_one({"job_id": job_id})["_id"]}, {"$set": {"status": "processing", "current_step": step, "progress": prog, "updated_at": datetime.utcnow()}})
            sleep(0.6)
        # produce a dummy render url (in real life, you'd run ffmpeg + models)
        render_url = f"/api/demo/render/{job_id}.mp4"
        db["videojob"].update_one({"job_id": job_id}, {"$set": {"status": "completed", "render_url": render_url, "updated_at": datetime.utcnow()}})
    except Exception as e:
        db["videojob"].update_one({"job_id": job_id}, {"$set": {"status": "failed", "error": str(e)}})


@app.post("/api/upload")
def upload_video(background_tasks: BackgroundTasks, file: UploadFile = File(...), email: Optional[str] = Form(None)):
    try:
        job_id = str(uuid4())
        filename = f"{job_id}_{file.filename}"
        in_path = os.path.join(UPLOAD_DIR, filename)
        with open(in_path, "wb") as f:
            f.write(file.file.read())
        # create job in db
        job = VideoJob(
            email=email,
            filename=filename,
            size_bytes=os.path.getsize(in_path),
            status="queued",
            progress=0,
            current_step="analyze_content",
        )
        # include job_id as separate field for easy lookup
        job_dict = job.model_dump()
        job_dict["job_id"] = job_id
        create_document("videojob", job_dict)
        # start background processing
        background_tasks.add_task(fake_ai_processing, job_id, in_path)
        return {"ok": True, "job_id": job_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    try:
        job = db["videojob"].find_one({"job_id": job_id})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        job["_id"] = str(job["_id"])  # make serializable
        return job
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/demo/render/{name}")
def get_demo_render(name: str):
    # Serve a static demo asset as placeholder output
    # In a real system this would stream the rendered file
    demo_url = "https://cdn.coverr.co/videos/coverr-northern-lights-6960/1080p.mp4"
    return {"url": demo_url}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        # Try to import database module
        from database import db as _db

        if _db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = _db.name if hasattr(_db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"

            # Try to list collections to verify connectivity
            try:
                collections = _db.list_collection_names()
                response["collections"] = collections[:10]  # Show first 10 collections
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    # Check environment variables
    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
