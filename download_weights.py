import requests
import os

url = "https://huggingface.co/Nekochu/Wav2Lip/resolve/main/wav2lip_gan.pth"
dest = r"C:\Users\Rodrigo Sousa\.gemini\antigravity\wav2lip_checkpoints\wav2lip_gan.pth"

print(f"Downloading from {url} to {dest}...")
r = requests.get(url, stream=True)
r.raise_for_status()

os.makedirs(os.path.dirname(dest), exist_ok=True)

total_size = int(r.headers.get('content-length', 0))
downloaded = 0

with open(dest, 'wb') as f:
    for chunk in r.iter_content(chunk_size=8192):
        if chunk:
            f.write(chunk)
            downloaded += len(chunk)
            # Log every 5% progress
            if total_size > 0:
                percent = int(100 * downloaded / total_size)
                if percent % 5 == 0:
                    print(f"Downloaded: {percent}% ({downloaded}/{total_size} bytes)", flush=True)
            else:
                print(f"Downloaded: {downloaded} bytes", flush=True)
print("Download finished!", flush=True)
