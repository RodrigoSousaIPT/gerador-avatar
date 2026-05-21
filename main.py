import os
import uuid
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from gtts import gTTS

app = FastAPI(title="Gerador de Avatar")

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
outputs_dir = os.path.join(os.path.dirname(__file__), "outputs")

os.makedirs(uploads_dir, exist_ok=True)
os.makedirs(outputs_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")
app.mount("/outputs", StaticFiles(directory=outputs_dir), name="outputs")
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open(os.path.join(static_dir, "index.html"), "r", encoding="utf-8") as f:
        return f.read()

@app.post("/generate")
async def generate_avatar(
    image: UploadFile = File(...),
    script: str = Form(...)
):
    try:
        # Save the uploaded image
        file_extension = image.filename.split(".")[-1]
        unique_id = str(uuid.uuid4())
        image_filename = f"{unique_id}.{file_extension}"
        image_path = os.path.join(uploads_dir, image_filename)
        
        with open(image_path, "wb") as f:
            f.write(await image.read())
            
        import requests
        
        # 1. GENERATE AUDIO FROM SCRIPT (VOICE.AI)
        audio_filename = f"{unique_id}.wav"
        audio_path = os.path.join(outputs_dir, audio_filename)
        
        url = 'https://dev.voice.ai/api/v1/tts/speech'
        headers = {
            'Authorization': 'Bearer vk_65aa98986b1c0153cb827e59f8901f28be1c8914ab5ab29a2bcaf25dcd640220',
            'Content-Type': 'application/json'
        }
        data = {
            'text': script,
            'model': 'voiceai-tts-v1-latest'
            'voice_id': '3e14a0dc-6735-48a4-a827-1f53a13fefd9'
        }
        
        tts_response = requests.post(url, headers=headers, json=data)
        if tts_response.status_code == 200:
            with open(audio_path, 'wb') as f:
                f.write(tts_response.content)
        else:
            raise Exception(f"Voice.AI API Error {tts_response.status_code}: {tts_response.text}")
        
        # 2. LOCAL AVATAR GENERATION (WAV2LIP)
        video_filename = f"{unique_id}.mp4"
        video_path = os.path.join(outputs_dir, video_filename)
        
        import subprocess
        import sys
        
        wav2lip_dir = os.path.join(os.path.dirname(__file__), "Wav2Lip")
        inference_script = "inference.py"
        checkpoint_path = r"C:\Users\Rodrigo Sousa\.gemini\antigravity\wav2lip_checkpoints\wav2lip_gan.pth"
        
        cmd = [
            sys.executable, inference_script,
            "--checkpoint_path", checkpoint_path,
            "--face", image_path,
            "--audio", audio_path,
            "--outfile", video_path
        ]
        
        env = os.environ.copy()
        print("A executar Wav2Lip...")
        process = subprocess.run(cmd, cwd=wav2lip_dir, env=env, capture_output=True, text=True)
        
        if process.returncode != 0:
            raise Exception(f"Erro no Wav2Lip: {process.stderr}\n\nSTDOUT: {process.stdout}")
        
        return JSONResponse(content={
            "success": True,
            "message": "Avatar de vídeo gerado com sucesso!",
            "image_url": f"/uploads/{image_filename}",
            "audio_url": f"/outputs/{audio_filename}",
            "video_url": f"/outputs/{video_filename}"
        })
        
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
