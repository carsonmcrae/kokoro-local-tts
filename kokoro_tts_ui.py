import hashlib
import subprocess
from pathlib import Path
import urllib.request

import gradio as gr

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "kokoro-v1.0.onnx"
VOICES_PATH = BASE_DIR / "voices-v1.0.bin"
TEXT_PROMPTS_DIR = BASE_DIR / "Text Prompts"
OUTPUT_DIR = BASE_DIR / "outputs"
PREVIEW_DIR = OUTPUT_DIR / "previews"
PREVIEW_TEXT_DIR = PREVIEW_DIR / "sample_texts"

MODEL_URL = "https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/kokoro-v1.0.onnx"
VOICES_URL = "https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/voices-v1.0.bin"


def download_file(url, path):
    print(f"Downloading {path.name}...")
    urllib.request.urlretrieve(url, path)
    print(f"Downloaded {path.name}")


def ensure_models():
    if not MODEL_PATH.exists():
        download_file(MODEL_URL, MODEL_PATH)

    if not VOICES_PATH.exists():
        download_file(VOICES_URL, VOICES_PATH)


OUTPUT_DIR.mkdir(exist_ok=True)
PREVIEW_DIR.mkdir(exist_ok=True)
PREVIEW_TEXT_DIR.mkdir(exist_ok=True)
TEXT_PROMPTS_DIR.mkdir(exist_ok=True)

VOICE_OPTIONS = [
    "af_alloy", "af_aoede", "af_bella", "af_heart", "af_jessica", "af_kore", "af_nicole", "af_nova",
    "af_river", "af_sarah", "af_sky", "am_adam", "am_echo", "am_eric", "am_fenrir", "am_liam",
    "am_michael", "am_onyx", "am_puck", "am_santa", "bf_alice", "bf_emma", "bf_isabella", "bf_lily",
    "bm_daniel", "bm_fable", "bm_george", "bm_lewis", "ef_dora", "em_alex", "em_santa", "ff_siwis",
    "hf_alpha", "hf_beta", "hm_omega", "hm_psi", "if_sara", "im_nicola", "jf_alpha", "jf_gongitsune",
    "jf_nezumi", "jf_tebukuro", "jm_kumo", "pf_dora", "pm_alex", "pm_santa", "zf_xiaobei", "zf_xiaoni",
    "zf_xiaoxiao", "zf_xiaoyi",
]
DEFAULT_VOICE = "bm_lewis"
DEFAULT_SPEED = 0.85
SAMPLE_TEXT = (
    "He didn’t realize anything was wrong at first. That was the problem. "
    "Everything looked normal, but something underneath it felt slightly off. "
    "He stopped, listened, and said quietly, ‘I don’t think this is new. I think I’ve been here before.’"
)


def check_setup() -> str:
    missing = []
    if not MODEL_PATH.exists():
        missing.append(MODEL_PATH.name)
    if not VOICES_PATH.exists():
        missing.append(VOICES_PATH.name)
    if missing:
        return "Missing required file(s): " + ", ".join(missing)
    return "Setup looks good."


def slug_speed(speed: float) -> str:
    return str(speed).replace('.', '_')


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def preview_paths(voice: str, speed: float, sample_text: str) -> tuple[Path, Path, str]:
    digest = text_hash(sample_text)
    base_name = f"preview_{voice}_{slug_speed(speed)}_{digest}"
    text_path = PREVIEW_TEXT_DIR / f"{base_name}.txt"
    audio_path = PREVIEW_DIR / f"{base_name}.wav"
    return text_path, audio_path, base_name


def run_kokoro(input_path: Path, output_path: Path, voice: str, speed: float) -> str:
    command = [
        "kokoro-tts",
        str(input_path),
        str(output_path),
        "--voice",
        voice,
        "--speed",
        str(speed),
        "--model",
        str(MODEL_PATH),
        "--voices",
        str(VOICES_PATH),
    ]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            cwd=str(BASE_DIR),
        )
    except FileNotFoundError:
        raise gr.Error("The 'kokoro-tts' command was not found. Activate your venv and make sure kokoro-tts is installed.")
    except subprocess.CalledProcessError as e:
        details = (e.stderr or e.stdout or "Unknown error").strip()
        raise gr.Error(f"Kokoro failed:\n\n{details}")
    return completed.stdout.strip() or "Audio generated successfully."


def refresh_prompt_files():
    files = sorted([p.name for p in TEXT_PROMPTS_DIR.glob("*.txt")])
    value = files[0] if files else None
    return gr.update(choices=files, value=value)


def generate_from_upload(uploaded_file, voice: str, speed: float):
    status = check_setup()
    if status != "Setup looks good.":
        raise gr.Error(status)
    if uploaded_file is None:
        raise gr.Error("Upload a .txt, .pdf, or .epub file first.")
    input_path = Path(uploaded_file)
    output_path = OUTPUT_DIR / f"{input_path.stem}_{voice}_{slug_speed(speed)}.wav"
    log = run_kokoro(input_path, output_path, voice, speed)
    return str(output_path), f"Saved to: {output_path}\n\n{log}"


def generate_from_browse_with_refresh(selected_file: str, voice: str, speed: float):
    status = check_setup()
    if status != "Setup looks good.":
        raise gr.Error(status)

    # Always refresh file list first
    files = sorted([p.name for p in TEXT_PROMPTS_DIR.glob("*.txt")])

    if not files:
        raise gr.Error("No .txt files found in Text Prompts.")

    # If selected file is missing (e.g., newly added), try to use it if it exists
    if selected_file:
        input_path = TEXT_PROMPTS_DIR / selected_file
        if not input_path.exists():
            raise gr.Error(f"Could not find: {input_path}")
    else:
        # fallback: use most recent file
        input_path = TEXT_PROMPTS_DIR / files[-1]
        selected_file = input_path.name

    output_path = OUTPUT_DIR / f"{input_path.stem}_{voice}_{slug_speed(speed)}.wav"
    log = run_kokoro(input_path, output_path, voice, speed)

    return (
        str(output_path),
        f"Saved to: {output_path}\n\n{log}",
        gr.update(choices=files, value=selected_file),
    )


def generate_voice_preview(voice: str, speed: float, sample_text: str):
    status = check_setup()
    if status != "Setup looks good.":
        raise gr.Error(status)
    if not sample_text.strip():
        raise gr.Error("Enter sample text first.")

    text_path, output_path, _ = preview_paths(voice, speed, sample_text)

    if output_path.exists() and text_path.exists():
        return str(output_path), f"Loaded cached preview: {output_path}"

    text_path.write_text(sample_text, encoding="utf-8")
    log = run_kokoro(text_path, output_path, voice, speed)
    return str(output_path), f"Preview saved to: {output_path}\nSample text saved to: {text_path}\n\n{log}"


def clear_preview_cache():
    removed = []
    for path in sorted(PREVIEW_DIR.glob("*.wav")):
        path.unlink(missing_ok=True)
        removed.append(path.name)
    for path in sorted(PREVIEW_TEXT_DIR.glob("*.txt")):
        path.unlink(missing_ok=True)
    if not removed:
        return None, "Preview cache is already empty."
    return None, f"Cleared preview cache. Removed {len(removed)} preview audio file(s)."


def batch_generate(voice: str, speed: float):
    status = check_setup()
    if status != "Setup looks good.":
        raise gr.Error(status)
    files = sorted(TEXT_PROMPTS_DIR.glob("*.txt"))
    if not files:
        raise gr.Error("No .txt files found in Text Prompts.")
    generated = []
    for input_path in files:
        output_path = OUTPUT_DIR / f"{input_path.stem}_{voice}_{slug_speed(speed)}.wav"
        run_kokoro(input_path, output_path, voice, speed)
        generated.append(output_path.name)
    latest = OUTPUT_DIR / generated[-1]
    summary = "Batch complete. Generated:\n\n" + "\n".join(generated)
    return str(latest), summary


with gr.Blocks(title="Local Kokoro TTS") as demo:
    gr.Markdown("# Local Kokoro TTS")
    gr.Markdown("Generate audio from uploaded files or files inside your Text Prompts folder.")

    with gr.Row():
        voice_dropdown = gr.Dropdown(
            choices=VOICE_OPTIONS,
            value=DEFAULT_VOICE,
            label="Voice",
        )
        speed_slider = gr.Slider(
            minimum=0.7,
            maximum=1.1,
            value=DEFAULT_SPEED,
            step=0.01,
            label="Speed",
        )

    with gr.Row():
        audio_output = gr.Audio(
            label="Audio preview / latest output",
            type="filepath",
            autoplay=True,
            buttons=[],
            interactive=False,
        )
        status_box = gr.Textbox(label="Status / log", lines=12)

    with gr.Tab("Browse Text Prompts"):
        browse_dropdown = gr.Dropdown(
            choices=sorted([p.name for p in TEXT_PROMPTS_DIR.glob("*.txt")]),
            label="Choose a file from Text Prompts",
        )
        with gr.Row():
            refresh_btn = gr.Button("Refresh file list")
            generate_browse_btn = gr.Button("Generate from selected file", variant="primary")

    with gr.Tab("Upload File"):
        uploaded_file = gr.File(
            label="Upload file",
            file_types=[".txt", ".pdf", ".epub"],
            type="filepath",
        )
        generate_upload_btn = gr.Button("Generate from uploaded file", variant="primary")

    with gr.Tab("Voice Preview"):
        preview_text = gr.Textbox(
            label="Sample text",
            value=SAMPLE_TEXT,
            lines=6,
        )
        with gr.Row():
            preview_btn = gr.Button("Preview selected voice", variant="secondary")
            clear_cache_btn = gr.Button("Clear preview cache")
        gr.Markdown("Preview files are cached in outputs/previews so repeat previews load much faster.")

    with gr.Tab("Batch"):
        gr.Markdown("Generate audio for every .txt file in the Text Prompts folder using the currently selected voice and speed.")
        batch_btn = gr.Button("Batch generate all .txt files", variant="secondary")

    refresh_btn.click(fn=refresh_prompt_files, outputs=[browse_dropdown])
    generate_browse_btn.click(
        fn=generate_from_browse_with_refresh,
        inputs=[browse_dropdown, voice_dropdown, speed_slider],
        outputs=[audio_output, status_box, browse_dropdown],
    )
    generate_upload_btn.click(
        fn=generate_from_upload,
        inputs=[uploaded_file, voice_dropdown, speed_slider],
        outputs=[audio_output, status_box],
    )
    preview_btn.click(
        fn=generate_voice_preview,
        inputs=[voice_dropdown, speed_slider, preview_text],
        outputs=[audio_output, status_box],
    )
    clear_cache_btn.click(
        fn=clear_preview_cache,
        outputs=[audio_output, status_box],
    )
    batch_btn.click(
        fn=batch_generate,
        inputs=[voice_dropdown, speed_slider],
        outputs=[audio_output, status_box],
    )

if __name__ == "__main__":
    ensure_models()
    demo.launch(inbrowser=True)
