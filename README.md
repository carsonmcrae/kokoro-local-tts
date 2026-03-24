# Local Kokoro TTS Web UI

A local text-to-speech tool using Kokoro with a simple web interface.

## Features

- 50+ voice options
- Adjustable speech speed
- Voice preview with caching (fast after first load)
- Batch processing support
- Upload or browse text files
- Automatic model download on first run

## Demo

Launch the app locally and open:

http://127.0.0.1:7860

Select a voice, adjust speed, and generate speech from text files or uploads.

## Setup

1. Navigate to project folder:

cd C:\tts

2. Create and activate virtual environment:

python -m venv venv  
venv\Scripts\activate  

3. Install dependencies:

pip install -r requirements.txt

## Run

python kokoro_tts_ui.py

On first run, required model files (~350MB) will be downloaded automatically.

## Usage

- Place `.txt` files in the **Text Prompts** folder to use the Browse feature  
- Or upload a file directly in the UI  
- Generated audio files are saved in the **outputs** folder  

## Controls

**Start the app**
1. Open Command Prompt  
2. Run: cd C:\tts  
3. Run: venv\Scripts\activate  
4. Run: python kokoro_tts_ui.py  

**Stop the app**
1. Go to the Command Prompt window running the app  
2. Press: Ctrl + C  
3. If prompted with “Terminate batch job (Y/N)?”, type: Y  

## Notes

- Voice previews are cached after first generation for faster playback  
- Model files are not included in the repo and will download automatically  