from fastapi import FastAPI, File, UploadFile, HTTPException, Request,Response
from stream.ocr_extract import *
from stream.timeextract import *
from stream.timeconversion import timeconvert
from fastapi.responses import JSONResponse
from moviepy.video.io.VideoFileClip import VideoFileClip
import os
import subprocess

app = FastAPI()

UPLOAD_DIR = "temp_videos"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

file_location = {}
time_storage = {}

# Upload video
@app.post("/upload/")
async def upload_video(file: UploadFile = File()):
    original_filename = file.filename
    file_location_path = f"{UPLOAD_DIR}/{original_filename}"  
    
    try:
        if not os.path.exists(UPLOAD_DIR):
            os.makedirs(UPLOAD_DIR)
        with open(file_location_path, "wb") as buffer:
            buffer.write(file.file.read())

        start_frame = frame_extract_1(file_location_path)
        end_frame = frame_extract_2(file_location_path)
        start_time = extract_timestamp(start_frame)
        end_time = extract_timestamp(end_frame)
        time_storage['start_time'] = start_time
        time_storage['end_time'] = end_time
        time_storage['file_path'] = file_location_path 

        if not start_time or not end_time:
            raise HTTPException(status_code=400, detail="Invalid start or end time extracted.")
            
        print(f"File saved at: {file_location_path}")  
        
    except Exception as e:
        print(f"Error during upload processing: {e}") 
        raise HTTPException(status_code=500, detail=str(e))
        
    return {
        "message": "File uploaded successfully", 
        "filename": original_filename,
        "filepath": file_location_path,  
        "Start Time": start_time, 
        "End Time": end_time
    }


# Trim video
@app.post("/trim_video")
async def trim_video(request: Request):
    body = await request.json()
    start_time_str = body.get("start_time_sec")
    end_time_str = body.get("end_time_sec")
    print(f"Start time : {start_time_str}")
    print(f"End time : {end_time_str}")

    if start_time_str is None or end_time_str is None:
        raise HTTPException(status_code=400, detail="Start or end time not provided.")
    
    try:
        video_path = time_storage.get("file_path")
        if not video_path or not os.path.exists(video_path):
            raise HTTPException(status_code=400, detail="Uploaded video file not found.")
        command_duration = ["ffmpeg", "-i", video_path]
        result = subprocess.run(command_duration, capture_output=True, text=True)
        duration_line = next((line for line in result.stderr.splitlines() if "Duration" in line), None)
        
        if not duration_line:
            raise HTTPException(status_code=400, detail="Could not retrieve video duration.")
        
        # Parse video duration
        duration_str = duration_line.split("Duration:")[1].strip().split(",")[0].strip()
        time_parts = duration_str.split(":")
        
        if len(time_parts) != 3:
            raise ValueError(f"Invalid duration format: {duration_str}")
        
        hours, minutes, seconds = time_parts
        seconds_parts = seconds.split(".")
        if len(seconds_parts) > 1:
            seconds = float(seconds_parts[0]) + float(f"0.{seconds_parts[1]}")
        else:
            seconds = float(seconds_parts[0])

        video_duration_sec = int(hours) * 3600 + int(minutes) * 60 + seconds
        print(f"Video duration: {video_duration_sec} seconds")

        # Now convert input times to seconds
        def time_to_seconds(time_str):
            try:
                time_obj = datetime.strptime(time_str, "%I:%M:%S %p")
                total_seconds = time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second
                video_start = datetime.strptime(time_storage['start_time'], "%I:%M:%S %p")
                video_start_seconds = video_start.hour * 3600 + video_start.minute * 60 + video_start.second
                return total_seconds - video_start_seconds
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid time format: {time_str}")

        start_time_sec = time_to_seconds(start_time_str)
        end_time_sec = time_to_seconds(end_time_str)

        print(f"Converted start time: {start_time_sec} seconds")
        print(f"Converted end time: {end_time_sec} seconds")

        # Validate times
        if start_time_sec < 0:
            raise HTTPException(status_code=400, detail="Start time is before video begins")

        if end_time_sec > video_duration_sec:
            raise HTTPException(status_code=400, detail=f"End time exceeds video duration ({video_duration_sec} seconds)")
        print(f"This is time storage : {time_storage}")
        video_path = time_storage.get("file_path")
        if not video_path or not os.path.exists(video_path):
            raise HTTPException(status_code=400, detail="Uploaded video file not found.")
        print(f"Video path: {video_path}")
        command_duration = ["ffmpeg", "-i", video_path]
        result = subprocess.run(command_duration, capture_output=True, text=True)
        
        # Log the full stderr output from FFmpeg for debugging
        print(f"FFmpeg stderr: {result.stderr}")
        duration_line = next((line for line in result.stderr.splitlines() if "Duration" in line), None)
        
        if not duration_line:
            raise HTTPException(status_code=400, detail="Could not retrieve video duration.")
        
        # Log the duration line we found
        print(f"Duration line: {duration_line}")

        try:
            # Get the part after 'Duration:' and split by commas
            duration_str = duration_line.split("Duration:")[1].strip().split(",")[0].strip()
            print(f"Extracted duration string: {duration_str}")  # Debug print
            
            time_parts = duration_str.split(":")
            
            # Ensure time_parts has exactly 3 elements (hours, minutes, seconds)
            if len(time_parts) != 3:
                raise ValueError(f"Invalid duration format: {duration_str}")
            hours, minutes, seconds = time_parts
            seconds_parts = seconds.split(".")
            if len(seconds_parts) > 1:
                seconds = float(seconds_parts[0]) + float(f"0.{seconds_parts[1]}")
            else:
                seconds = float(seconds_parts[0])
            video_duration_sec = int(hours) * 3600 + int(minutes) * 60 + seconds
            print(f"Parsed video duration: {video_duration_sec} seconds")

        except Exception as e:
            print(f"Failed to parse video duration: {str(e)}")
            print(f"Duration line was: {duration_line}")
            raise HTTPException(status_code=400, detail="Failed to parse video duration.")
        if end_time_sec > video_duration_sec:
            raise HTTPException(status_code=400, detail="End time exceeds video duration.")
        trimmed_video_path = f"{UPLOAD_DIR}/trimmed_video.mp4"
        if not os.path.exists(UPLOAD_DIR):
            os.makedirs(UPLOAD_DIR)

        # FFmpeg command to trim the video
        command = [
            "ffmpeg",
            "-ss", str(start_time_sec),
            "-i", video_path,
            "-t", str(end_time_sec - start_time_sec),
            "-c:v", "libx264",
            "-c:a", "aac",
            "-strict", "experimental",
            "-y",  
            "-loglevel", "debug",  
            trimmed_video_path
        ]
        print(f"Running FFmpeg command: {' '.join(command)}")

        # Run the FFmpeg command
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"FFmpeg Output: {result.stdout}")
        print(f"FFmpeg Error: {result.stderr}")

        # Read the trimmed video
        with open(trimmed_video_path, "rb") as f:
            trimmed_video = f.read()

        os.remove(trimmed_video_path)
    
        return Response(
            content=trimmed_video,
            media_type="video/mp4",
            headers={
                'Content-Disposition': f'attachment; filename="trimmed_video.mp4"'
            }
        )
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e.stderr}")
        raise HTTPException(status_code=500, detail=f"Error during trimming: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during trimming: {str(e)}")


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
