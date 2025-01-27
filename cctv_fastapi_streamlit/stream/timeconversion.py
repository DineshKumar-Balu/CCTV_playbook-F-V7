import os
import subprocess

## converting h64 format

def convert_h64(input_video_path,output_video_path):
    ffmpeg_path = os.path.join(os.path.dirname(__file__), "ffmpeg-v1", "bin", "ffmpeg.exe")
    command = [
        ffmpeg_path, '-y',
        '-i', input_video_path,
        '-c:v', 'libx264',
        output_video_path
    ]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def timeconvert(file_vedio):
    if file_vedio is not None:
        assets_dir = os.path.join('.', 'assets')
        os.makedirs(assets_dir, exist_ok=True)
        video_path = os.path.join(assets_dir, 'out.mp4')
        h64_path = os.path.join(assets_dir, 'h64.mp4')

        with open(video_path, 'wb') as file:
            file.write(file_vedio.read())

        convert_h64(video_path,h64_path)
        return h64_path
