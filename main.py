import os
import uuid
import base64
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from gtts import gTTS

app = FastAPI(title="Gerador de Avatar")

# Detect if running on Vercel
IS_VERCEL = "VERCEL" in os.environ

static_dir = os.path.join(os.path.dirname(__file__), "static")

if IS_VERCEL:
    # Use /tmp for uploads and outputs on Vercel (read-only filesystem bypass)
    uploads_dir = "/tmp/uploads"
    outputs_dir = "/tmp/outputs"
else:
    uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
    outputs_dir = os.path.join(os.path.dirname(__file__), "outputs")

# Create directories only if we have write permissions
try:
    os.makedirs(uploads_dir, exist_ok=True)
    os.makedirs(outputs_dir, exist_ok=True)
except Exception as e:
    print(f"Warning: Could not create directories: {e}")

# Mount static files
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Mount uploads and outputs
try:
    app.mount("/outputs", StaticFiles(directory=outputs_dir), name="outputs")
    app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")
except Exception as e:
    print(f"Warning: Could not mount uploads/outputs directories: {e}")

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
        # Read image bytes first (needed for saving or base64)
        image_bytes = await image.read()
        
        import requests
        
        # 1. GENERATE AUDIO FROM SCRIPT (VOICE.AI)
        url = 'https://dev.voice.ai/api/v1/tts/speech'
        headers = {
            'Authorization': 'Bearer vk_65aa98986b1c0153cb827e59f8901f28be1c8914ab5ab29a2bcaf25dcd640220',
            'Content-Type': 'application/json'
        }
        data = {
            'text': script,
            'model': 'voiceai-tts-v1-latest',
            'voice_id': '3e14a0dc-6735-48a4-a827-1f53a13fefd9'
        }
        
        tts_response = requests.post(url, headers=headers, json=data)
        if tts_response.status_code != 200:
            raise Exception(f"Voice.AI API Error {tts_response.status_code}: {tts_response.text}")
            
        audio_bytes = tts_response.content
        
        if IS_VERCEL:
            # On Vercel, bypass local filesystem and Wav2Lip execution, return base64
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            content_type = image.content_type or "image/png"
            
            return JSONResponse(content={
                "success": True,
                "message": "Áudio gerado com sucesso (Vercel Mode)!",
                "image_url": f"data:{content_type};base64,{image_b64}",
                "audio_url": f"data:audio/wav;base64,{audio_b64}",
                "video_url": None
            })
            
        # Local Mode: Save files and run Wav2Lip
        unique_id = str(uuid.uuid4())
        file_extension = image.filename.split(".")[-1] if image.filename else "png"
        image_filename = f"{unique_id}.{file_extension}"
        image_path = os.path.join(uploads_dir, image_filename)
        
        with open(image_path, "wb") as f:
            f.write(image_bytes)
            
        audio_filename = f"{unique_id}.wav"
        audio_path = os.path.join(outputs_dir, audio_filename)
        with open(audio_path, 'wb') as f:
            f.write(audio_bytes)
            
        # 2. LOCAL AVATAR GENERATION (WAV2LIP)
        video_filename = f"{unique_id}.mp4"
        video_path = os.path.join(outputs_dir, video_filename)
        
        import subprocess
        import sys
        
        wav2lip_dir = os.path.join(os.path.dirname(__file__), "Wav2Lip")
        inference_script = "inference.py"
        
        # Check if local model weights exist in C: drive or relative path
        checkpoint_path = r"C:\Users\Rodrigo Sousa\.gemini\antigravity\wav2lip_checkpoints\wav2lip_gan.pth"
        if not os.path.exists(checkpoint_path):
            checkpoint_path = os.path.join(os.path.dirname(__file__), "wav2lip_gan.pth")
            
        if not os.path.exists(checkpoint_path):
            print(f"Checkpoint não encontrado. Devolvendo apenas imagem e áudio.")
            return JSONResponse(content={
                "success": True,
                "message": "Áudio gerado com sucesso! (Vídeo desativado: modelo não encontrado)",
                "image_url": f"/uploads/{image_filename}",
                "audio_url": f"/outputs/{audio_filename}",
                "video_url": None
            })
            
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
            print(f"Erro no Wav2Lip: {process.stderr}\n\nSTDOUT: {process.stdout}")
            return JSONResponse(content={
                "success": True,
                "message": "Áudio gerado com sucesso! (Vídeo falhou)",
                "image_url": f"/uploads/{image_filename}",
                "audio_url": f"/outputs/{audio_filename}",
                "video_url": None
            })
            
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

