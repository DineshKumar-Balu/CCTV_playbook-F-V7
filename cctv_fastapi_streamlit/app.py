import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from io import BytesIO

api_url = "http://localhost:8000"
video_bytes = None

# Upload video function
def upload_video():
    global video_bytes 
    uploaded_file = st.file_uploader("Choose a video...", type=["mp4", "avi", "mov"], key="video_upload", label_visibility="collapsed")
    
    start_time = "00:00:00"
    end_time = "00:00:00"
    message = "Please Upload the video File!!"

    if uploaded_file is not None:
        # Persist the uploaded video file in memory
        video_bytes = BytesIO(uploaded_file.getvalue())
        files = {"file": uploaded_file.getvalue()}
        response = requests.post(f"{api_url}/upload/", files=files)

        if response.status_code == 200:
            start_time = response.json().get("Start Time", "Not available")
            end_time = response.json().get("End Time", "Not available")
            message = "Upload successful."
        else:
            st.error("Error uploading the file")
            message = "Upload failed."

    return start_time, end_time, message

def upload_file(csv_file):
    if csv_file is not None:  
        df = pd.read_csv(csv_file)
        return df
    else:
        st.error("No file uploaded or invalid file type.")  
        return None

# Function to input jump time and calculate the jump in seconds
def jump_time_input(jump_time, url):
    payload = {"jump_time": jump_time}
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            jump_sec = response.json().get("jump_offset")
            if jump_sec is not None:
                try:
                    jump_sec = int(jump_sec)  
                    return jump_sec
                except ValueError:
                    st.error("Invalid jump offset received from the server.")
            else:
                st.error("Jump offset not found in the server response.")
        else:
            st.error("Could not jump the video.")
    except Exception as ex:
        st.error(f"Failed to jump time: {ex}")
    return 0

def validate_time(jump):
    try:
        
        datetime.strptime(jump, "%H:%M:%S")  
        return True
    except ValueError:
        try:
            datetime.strptime(jump, "%I:%M:%S %p")  
            return True
        except ValueError:
            return False
        

# Main function to run Streamlit UI
def main():
    global video_bytes
    st.title("Video Playback Tool")

    if 'video_time' not in st.session_state:
        st.session_state.video_time = 0 

    with st.sidebar:
        # File uploader for CSV
        csv_file = st.file_uploader("Select the CSV file: ", type=['csv'])
        extract_time_csv = upload_file(csv_file) if csv_file else None

        start_time, end_time, message = upload_video()

        if extract_time_csv is not None:
            columns = extract_time_csv.columns.tolist()
            selected_column = st.selectbox("Select Column:", columns)
            unique_values = extract_time_csv[selected_column].unique().tolist()
            selected_value = st.selectbox("Select Value:", unique_values)

        col3, col4 = st.columns([2, 6])
        col4.write("Trim Option: ")
        trim_start_time = st.text_input(label="Start Time", placeholder="Enter start time (HH:MM:SS)")
        trim_end_time = st.text_input(label="End Time", placeholder="Enter end time (HH:MM:SS)")
        
        col1, col2,col3 = st.columns([1,5,6])
        # Initialize session state for download visibility
        if 'show_download_button' not in st.session_state:
            st.session_state.show_download_button = False

        if col2.button("Trim Video"):
            start_sec = trim_start_time
            end_sec = trim_end_time

            if start_sec is not None and end_sec is not None and end_sec > start_sec:
                payload = {
                    "start_time_sec": start_sec,
                    "end_time_sec": end_sec
                }
                response = requests.post(f"{api_url}/trim_video", json=payload)
                if response.status_code == 200:
                    # st.success("Video trimmed successfully. Downloading...")
                    trimmed_video = response.content
                    # Set session state to show the download button
                    st.session_state.show_download_button = True
                    st.session_state.trimmed_video = trimmed_video
                else:
                    st.error("Failed to trim the video.")
                    st.session_state.show_download_button = False
            else:
                st.error("Invalid start and end times. Ensure end time is greater than start time.")
                st.session_state.show_download_button = False

        if st.session_state.show_download_button:
            col3.download_button(label="Download", 
                                data=st.session_state.trimmed_video, 
                                file_name="trimmed_video.mp4", 
                                mime="video/mp4")

    # Display video with updated start time
    if video_bytes:
        st.video(video_bytes, start_time=st.session_state.video_time, autoplay=True)

    buf1, buf2, buf3 = st.columns([9, 8, 7])
    with buf2:
        st.write(message)

    col1, col2, col3, col4 = st.columns([7, 7, 2, 5])
    with col1:
        st.write(f"Start Time: {start_time}")
    with col2:
        jump_time = st.text_input("Enter the Jump Time:")
    with col4:
        st.write(f"End Time: {end_time}")

    url = "http://localhost:8000/jump_time"

    buff1, buff2 = st.columns([7, 10])
    with buff2:
        if st.button("Jump time"):
            if validate_time(jump_time):
                jump_sec = jump_time_input(jump_time, url)
                if jump_sec >= 0:
                    st.session_state.video_time = jump_sec
                else:
                    st.error("Failed to calculate jump time offset.")
            else:
                st.error("Invalid time format. Please use HH:MM:SS format (e.g., 01:15:30 PM).")

    if extract_time_csv is not None and selected_value:
        filtered_df = extract_time_csv[extract_time_csv[selected_column] == selected_value]
        st.subheader(f"Uploaded File Data :")
        st.write(filtered_df)

        

if __name__ == "__main__":
    main()
