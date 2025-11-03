import gradio as gr
import requests
import json
import os

def generate_audio(text, voice="belinda"):
    url = "http://10.6.1.15:8010/v1/audio/speech"
    payload = {
        "model": "higgs-audio-v2-generation-3B-base",
        "voice": voice,
        "input": text,
        "response_format": "wav",
        "max_tokens": 2048,
        "temperature": 0.6,
        "top_p": 0.8
    }
    prompt_str = json.dumps(payload, indent=2)
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            output_path = os.path.join(os.getcwd(), "temp_audio.wav")
            with open(output_path, "wb") as f:
                f.write(response.content)
            return output_path, None, prompt_str
        return None, f"Error: {response.status_code} - {response.text}", prompt_str
    except Exception as e:
        return None, f"Connection error: {str(e)}", prompt_str

with gr.Blocks(title="Higgs Audio 2 Voices") as demo:
    gr.Markdown("# 🎤 Higgs Audio 2 - Voice Playground")
    gr.Markdown("Type text, pick a voice, and hear it!")
    text_input = gr.Textbox(label="Text to Speak", placeholder="Yo, Mikey, let’s make some noise!", lines=2)
    voice_dropdown = gr.Dropdown(choices=["belinda", "broom_salesman", "mabel", "vex", "en_woman", "zh_man_sichuan", "chadwick", "en_man"], label="Voice", value="belinda")
    generate_btn = gr.Button("Generate & Play")
    audio_output = gr.Audio(label="Generated Audio", type="filepath")
    status_msg = gr.Textbox(label="Status", interactive=False)
    prompt_display = gr.Textbox(label="Prompt Sent to Server", interactive=False, lines=8)
    generate_btn.click(fn=generate_audio, inputs=[text_input, voice_dropdown], outputs=[audio_output, status_msg, prompt_display])

demo.launch(server_name="0.0.0.0", server_port=7860)