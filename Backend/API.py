from fastapi import FastAPI, UploadFile, File, Form,BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
from RAM_Analysis import RAM_Analysis
import os
from pathlib import Path
import io
import cv2

app = FastAPI()
emoticon = ["😊","😡","😎","🐶","👋","🌍"]

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "..\public\output"
os.makedirs(UPLOAD_DIR, exist_ok=True)

model = RAM_Analysis("merged_classification.csv")
# overlay_mask = [
#         "0 0.548750 0.060000 0.591250 0.060000 0.583750 0.397778 0.538750 0.400000",
#         "0 0.592500 0.400000 0.736250 0.177778 0.767500 0.217778 0.617500 0.442222",
#         "0 0.621250 0.464444 0.835000 0.484444 0.840000 0.551111 0.623750 0.524444",
#         "0 0.618750 0.551111 0.772500 0.840000 0.743750 0.893333 0.591250 0.604444",
#         "0 0.367500 0.853333 0.338750 0.788889 0.511250 0.535556 0.535000 0.584444",
#         "0 0.543750 0.593333 0.571250 0.593333 0.570000 0.993333 0.530000 0.993333",
#         "0 0.510000 0.526667 0.286250 0.504444 0.291250 0.433333 0.510000 0.466667",
#         "0 0.371250 0.186667 0.401250 0.151111 0.527500 0.393333 0.505000 0.457778",
#     ]


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/getRandomEmoticon")
def RandomEmoticon():
    emoticon.append(emoticon[0])
    emoticon.pop(0)
    return {"emoticon": emoticon[0]}

@app.get("/getVideoProgress")
def VideoProgress():
    return {"progress": model.progress_video}



@app.post("/upload_chunk/")
async def upload_chunk(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    chunk_index: int = Form(...),
    total_chunks: int = Form(...),
    filename: str = Form(...),
    overlay_mask:str = Form(...)
):
    temp_dir = "temp_chunks"
    os.makedirs(temp_dir, exist_ok=True)

    chunk_path = os.path.join(temp_dir, f"{filename}.part{chunk_index}")

    with open(chunk_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # ✅ Merge when last chunk arrives
    if chunk_index + 1 == total_chunks:
        final_path = os.path.join(UPLOAD_DIR, filename)

        with open(final_path, "wb") as final_file:
            for i in range(total_chunks):
                part_path = os.path.join(temp_dir, f"{filename}.part{i}")
                with open(part_path, "rb") as part_file:
                    final_file.write(part_file.read())
                os.remove(part_path)

        # ✅ Run heavy AI processing in background (NON-BLOCKING)
        background_tasks.add_task(
            model.process_video,
            final_path,
            overlay_mask.split(";")
        )

    return {
        "status": "chunk received",
        "chunk": chunk_index
    }


@app.get("/getOutputPath")
def getOutputPath():
    FOLDER = "..\public\output"  # change to your folder
    video_ext = ('.mp4', '.avi', '.mov', '.mkv',".webm")

    video_paths = [
        os.path.join("output", f)

        for f in os.listdir(FOLDER)
        
        if f.lower().endswith(video_ext)
    ]

    return {"paths":video_paths}

@app.post("/get_first_frame/")
async def get_first_frame(file: UploadFile = File(...)):
    # Save temp video
    video_path = f"temp_{file.filename}"
    with open(video_path, "wb") as f:
        content = await file.read()
        f.write(content)

    cap = cv2.VideoCapture(video_path)
    success, frame = cap.read()
    cap.release()

    if not success:
        return {"error": "Failed to read video"}

    # Convert frame to JPG in memory
    _, buffer = cv2.imencode(".jpg", frame)
    io_buf = io.BytesIO(buffer)

    return StreamingResponse(io_buf, media_type="image/jpeg")