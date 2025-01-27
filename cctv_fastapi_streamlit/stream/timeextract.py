import cv2 
from stream.ocr_extract import *


def frame_extract_1(curr_vedio):
    video = cv2.VideoCapture(curr_vedio)
    if not video.isOpened():
        print("Error: Could not open video.")
        return None
    
    video.set(cv2.CAP_PROP_POS_FRAMES, 0)   
    ret, frame = video.read()

    if not ret:
        print("Error: Could not read frame from start.")
        return None
    cv2.imwrite('frame_first.png', frame)
    return frame

def frame_extract_2(curr_vedio):
    video = cv2.VideoCapture(curr_vedio)
    if not video.isOpened():
        print("Error : could not open the video")
        return None
    count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    video.set(cv2.CAP_PROP_POS_FRAMES,count - 1 )
    ret, frame = video.read()

    if not ret:
        print("Error: could not read the frame from end")
        return None
    return frame