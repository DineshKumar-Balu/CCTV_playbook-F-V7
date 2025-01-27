from fastapi import FastAPI, File, UploadFile, HTTPException,Request
from stream.ocr_extract import *
from stream.timeextract import *
from stream.timeconversion import timeconvert
from fastapi.responses import JSONResponse
import os

app = FastAPI()
UPLOAD_DIR = "temp_videos"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

file_location ={}
time_storage = {}

# Upload video
@app.post("/upload/")
async def upload_video(file: UploadFile = File()):
    file_location = f"{UPLOAD_DIR}/{file.filename}"
    file_data = {'File_location': file_location}  
    try:
        with open(file_location, "wb") as buffer:
            buffer.write(file.file.read())
        start_frame = frame_extract_1(file_location)
        end_frame = frame_extract_2(file_location)
        start_time = extract_timestamp(start_frame)
        end_time = extract_timestamp(end_frame)
        # print(start_time)
        time_storage['start_time'] = start_time
        time_storage['end_time'] = end_time
        if not start_time or not end_time:
            raise HTTPException(status_code=400, detail="Invalid start or end time extracted.")
    except Exception as e:
        print(f"Error during upload processing: {e}") 
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(file_location):
            os.remove(file_location)
        # print(end_time)
    return {"message": "File uploaded successfully", "filename": file.filename, "Start Time": start_time, "End Time": end_time}


# Calculate jump offset
@app.post("/jump_time")
async def calculate_jump(request: Request):
    body = await request.json()
    jump_time_in = body.get("jump_time")
    
    if jump_time_in is None:
        raise HTTPException(status_code=400, detail="Jump time not provided")
    
    start_time = time_storage.get("start_time")
    end_time = time_storage.get("end_time")
    
    try:
        curr_jump_sec, start_time_sec, end_time_sec = jump_time(jump_time_in, start_time, end_time, file_location)
        print(f"Fast API extracted the jump sec: {curr_jump_sec}")
        return {"jump_offset": curr_jump_sec}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing jump time: {str(e)}")
