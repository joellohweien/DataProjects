from IPython.display import display, Audio
from PIL import Image
from moviepy.editor import VideoFileClip, AudioFileClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
import cv2 # read video with open CV
import base64, io, openai, os, requests, streamlit as st, tempfile, json

# read in api_key
openai.api_key = st.secrets["api_key"]

# Step 1: Turn video into frames

def video_to_frames(video_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmpfile:
        tmpfile.write(video_file.read())
        video_filename = tmpfile.name
    
    video_duration = VideoFileClip(video_filename).duration

    video = cv2.VideoCapture(video_filename)
    base64Frames = []

    while video.isOpened():
        success, frame = video.read()
        if not success:
            break
        _, buffer = cv2.imencode(".jpg", frame)
        base64Frames.append(base64.b64encode(buffer).decode("utf-8"))
    
    video.release()
    print(len(base64Frames), 'frames red for analysis.')
    return base64Frames, video_filename, video_duration

# Step 2: Generate stories based on frames with GPT4 Turbo
# one second = 24 frames

def frames_to_story(base64Frames, prompt):
    PROMPT_MESSAGES = [
        {
            "role": "user",
            "content": [
                prompt,
                *map(lambda x: {"image": x, "resize": 768},
                     base64Frames[0::132]),
            ],
        },
    ]
    params = {
        "model": "gpt-4-vision-preview",
        "messages": PROMPT_MESSAGES,
        "max_tokens": 1000,
    }

    result = openai.chat.completions.create(**params)
    print(result.choices[0].message.content)
    return result.choices[0].message.content


## Streamlit UI
def main():
    st.set_page_config(page_title="Short Form Video Analyser", page_icon=":tv:")

    st.header("Short Form Video Analyser")

    uploaded_file = st.file_uploader("Upload your video")

    # Adjust column widths as needed for your layout
    col_video, col_prompt = st.columns([1, 2])

    with col_video:
        if uploaded_file is not None:
            # Use CSS to adjust video size
            st.markdown(
                f"""
                <style>
                .video-container {{
                    width: 50%; 
                }}
                </style>
                """,
                unsafe_allow_html=True
            )
            st.video(uploaded_file)

    with col_prompt:
        # Use markdown to format prompt text
        prompt = st.text_area(
            "Prompt for GPT (user editable)",
            value="You are a video editor for a creative agency.\n\n"
                  "These are the frames from a video that you have been "
                  "tasked to replicate for our brand. \n\n"
                  "Provide a report, describing the content, with details on "
                  "the elements being used to maximise engagement.",
            height=300
        )

    if st.button('Click for Report', type="primary") and uploaded_file is not None:
        with st.spinner("Processing Video..."):
            base64Frames, video_filename, video_duration = video_to_frames(
                uploaded_file
            )

            # Generate the story/report from frames
            report = frames_to_story(base64Frames, prompt)

            # Display the generated report
            st.subheader("Generated Report")
            st.write(report)

if __name__ == '__main__':
    main()
