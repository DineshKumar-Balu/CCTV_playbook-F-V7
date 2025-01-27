import pytesseract
from PIL import Image
from stream.timeextract import *
import cv2
import re
from datetime import datetime


def extract_timestamp(frame, x=0, y=0, w=850, h=50):
    try:
        timestamp_crop = frame[y:y+h, x:x+w]
        timestamp_grey = cv2.cvtColor(timestamp_crop, cv2.COLOR_BGR2GRAY)
        _, timestamp_thresh = cv2.threshold(timestamp_grey, 127, 255, cv2.THRESH_BINARY)
        candidate_str = pytesseract.image_to_string(timestamp_thresh, config='--psm 6')
        print("Extracted Text:", candidate_str)
        cropped_img_path = "stream/assets/cropped_img.png"
        cv2.imwrite(cropped_img_path, timestamp_crop)
        regex_str = r'Date:\s(\d{4}-\d{2}-\d{2})\sTime:\s(\d{2}:\d{2}:\d{2}\s(?:AM|PM))\sFrame:\s(\d{2}:\d{2}:\d{2}:\d{2})'
        match = re.search(regex_str, candidate_str)
        
        if match:
            date_str, time_str, frame_str = match.groups()
            return time_str
    except Exception as e:
        print(f"Error extracting timestamp: {e}")
    return None


def jump_time(jump_time, start_time, end_time, video_path):
    update_jump_time = datetime.strptime(jump_time, "%I:%M:%S %p")
    update_start_time = datetime.strptime(start_time, "%I:%M:%S %p")
    update_end_time = datetime.strptime(end_time, "%I:%M:%S %p")
    
    jump_sec = update_jump_time.hour * 3600 + update_jump_time.minute * 60 + update_jump_time.second
    start_time_sec = update_start_time.hour * 3600 + update_start_time.minute * 60 + update_start_time.second
    end_time_sec = update_end_time.hour * 3600 + update_end_time.minute * 60 + update_end_time.second
    
    print(f"jump sec = {jump_sec}")
    print(f"start time sec = {start_time_sec}")
    print(f"end time sec = {end_time_sec}")
    
    if start_time_sec <= jump_sec <= end_time_sec:
        curr_jump_sec = jump_sec - start_time_sec
        print(f"curr_jump_sec: {curr_jump_sec}")
    elif jump_sec < start_time_sec:
        curr_jump_sec = 0  
        print(f"curr_jump_sec: {curr_jump_sec}")
    elif jump_sec > end_time_sec:
        curr_jump_sec = end_time_sec - start_time_sec
        print(f"curr_jump_sec: {curr_jump_sec}")  
    
    return curr_jump_sec , start_time_sec ,end_time_sec



