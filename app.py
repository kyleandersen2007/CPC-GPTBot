from flask import Flask, render_template, request, send_file, jsonify
from openai import OpenAI
from dotenv import load_dotenv
import os
import io
import soundfile as sf
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs

import uuid

load_dotenv()
app = Flask(__name__)

previous_questions_and_answers = []

API_KEY = os.environ.get("OPEN_API_KEY")

clientVoice = ElevenLabs(
    api_key=os.environ.get("ELEVENLABS_KEY"),
)

def read_event_info(file_path):
    with open(file_path, 'r') as file:
        event_info = file.read()
    return event_info

models_info = {
    "gpt-3.5-turbo": {
        "name": "Max Spillner",
        "profile_pic": "static/max.jpg",
        "prompt": read_event_info("schedule.txt"),
    },
    "gpt-4-turbo": {
        "name": "Kyle Andersen",
        "profile_pic": "static/kyle.jpg",
        "prompt": read_event_info("schedule.txt"),
    },
}

def generate_audio(text):
    response = clientVoice.text_to_speech.convert(
        voice_id="mMTppeGIOz287223FYmf",
        optimize_streaming_latency="0",
        output_format="mp3_22050_32",
        text=text,
        model_id="eleven_multilingual_v2",
        voice_settings=VoiceSettings(
            stability=0.5,
            similarity_boost=0.85,
            style=0.5,
            use_speaker_boost=True,
        ),
    )

    audio_data = io.BytesIO()
    for chunk in response:
        audio_data.write(chunk)
    audio_data.seek(0)

    audio_array, sample_rate = sf.read(audio_data)
    return audio_array, sample_rate

@app.route("/", methods=["GET"])
def index():
    global previous_questions_and_answers
    previous_questions_and_answers = []
    return render_template('index.html')

AUDIO_FOLDER = "audio_files"

@app.route("/get", methods=["POST"])
def chat():
    global previous_questions_and_answers
    user_input = request.form["msg"]
    selected_model = request.form["model_select"]

    response_text = GetResponse(user_input, selected_model)
    previous_questions_and_answers.append((user_input, response_text))

    audio_data, sample_rate = generate_audio(response_text)
    audio_file_name = str(uuid.uuid4()) + ".mp3"
    audio_file_path = os.path.join(AUDIO_FOLDER, audio_file_name)
    sf.write(audio_file_path, audio_data, sample_rate)

    return jsonify(response=response_text, audio_url="/audio/" + audio_file_name)

from flask import send_from_directory

@app.route("/audio/<filename>")
def audio(filename):
    return send_from_directory(AUDIO_FOLDER, filename)


def GetResponse(prompt, model):
    global previous_questions_and_answers
    client = OpenAI(api_key=API_KEY)

    MODEL = None
    
    if model == "gpt-3.5-turbo":
        MODEL = "gpt-3.5-turbo"
    elif model == "gpt-4-turbo":
        MODEL = "gpt-3.5-turbo"
    
    messages = [
        { "role": "system", "content": models_info[model]["prompt"] },
    ]
    
    for question, answer in previous_questions_and_answers[-100:]:
        messages.append({ "role": "user", "content": question })
        messages.append({ "role": "assistant", "content": answer })
    
    messages.append({ "role": "user", "content": prompt })

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.5,
        max_tokens=50  
    )

    r = response.choices[0].message.content
    previous_questions_and_answers.append((prompt, r))

    return r

if __name__ == '__main__':
    port = 5050
    app.run('0.0.0.0', port)