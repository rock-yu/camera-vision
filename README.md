# Camera Vision

Describe your laptop camera feed with a vision model running locally through
[Ollama](https://ollama.com/). Camera frames, prompts, and model responses stay on your machine
when Ollama and any downstream speech tool are local.

## Requirements

- macOS with camera access enabled for your terminal application
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Ollama **0.24.0** when using the default `llama3.2-vision` model
- A local Ollama vision model; the default is `llama3.2-vision`

The Python code uses portable OpenCV APIs, but this first release documents and targets macOS.

> [!IMPORTANT]
> The default model currently requires Ollama **0.24.0**. Newer releases can fail with
> `unknown model architecture: 'mllama'`; see
> [ollama/ollama#16490](https://github.com/ollama/ollama/issues/16490). Do not install or upgrade
> Ollama with Homebrew if you intend to use `llama3.2-vision`, because Homebrew installs the latest
> release. Alternatively, keep current Ollama and select a supported vision model with `--model`.

## Setup

### 1. Install the compatible Ollama version

Download
[Ollama-darwin.zip for v0.24.0](https://github.com/ollama/ollama/releases/download/v0.24.0/Ollama-darwin.zip),
extract it, move **Ollama.app** to **Applications**, and launch it. If a newer Ollama version is
already installed, quit it and replace the application before continuing.

Verify the server and CLI are both using the compatible version:

```bash
ollama --version
# ollama version is 0.24.0
```

Avoid accepting an Ollama update while this compatibility workaround is required. If the desktop
application is not running the server, start it from a terminal with `ollama serve`.

### 2. Pull the model and install Python dependencies

```bash
ollama pull llama3.2-vision
uv sync
```

Confirm the model can load before troubleshooting the camera application:

```bash
ollama run llama3.2-vision "Say ready."
```

If you prefer a newer Ollama release, install it normally, pull a vision model supported by that
release, and pass its name explicitly:

```bash
ollama pull qwen2.5vl:3b
uv run camera-vision --model qwen2.5vl:3b
```

### 3. Run Camera Vision

Run the application:

```bash
uv run camera-vision
```

On first use, macOS may request camera access. If it does not, open **System Settings > Privacy &
Security > Camera** and enable access for the terminal or IDE running the command.

## Usage

The default mode shows a preview, performs an initial automatic analysis, repeats every five
seconds, and also accepts manual captures:

- **Space**: describe the current frame
- **Q**, **Shift-Q**, or **Escape**: quit

Manual capture only:

```bash
uv run camera-vision --mode manual
```

Automatic analysis every 10 seconds:

```bash
uv run camera-vision --mode interval --interval 10
```

Headless timed analysis:

```bash
uv run camera-vision --mode interval --interval 10 --no-preview
```

Use another camera, model, prompt, or Ollama server:

```bash
uv run camera-vision \
  --camera-index 1 \
  --model moondream \
  --host http://127.0.0.1:11434 \
  --prompt "Describe obstacles and changes in the room." \
  --timeout 90
```

`OLLAMA_HOST` is used when `--host` is omitted.

### Pipe descriptions to text-to-speech

`--output description` writes one normalized line per successful description to stdout. Startup
messages, controls, progress, and errors go to stderr, so stdout can be piped safely:

```bash
uv run camera-vision \
  --mode interval \
  --interval 10 \
  --no-preview \
  --output description |
while IFS= read -r description; do
  say "$description"
done
```

Replace macOS `say` with any local text-to-speech command or model that accepts text. The
application does not install or launch a speech engine itself.

### Built-in local speech

Speech is optional and disabled by default. Install the neural speech extra:

```bash
uv sync --extra speech
```

Download the Kokoro model and preset voices to the default local cache:

```bash
mkdir -p ~/.cache/camera-vision
curl -L \
  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/kokoro-v1.0.onnx \
  -o ~/.cache/camera-vision/kokoro-v1.0.onnx
curl -L \
  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/voices-v1.0.bin \
  -o ~/.cache/camera-vision/voices-v1.0.bin
```

Run a narrated demo with a cadence suited to the observed `llama3.2-vision` latency:

```bash
uv run --extra speech camera-vision \
  --speech \
  --speech-engine auto \
  --speech-voice af_sarah \
  --speech-rate 1.0 \
  --mode interval \
  --interval 20 \
  --prompt "Describe the most important visible objects or changes in one short sentence."
```

The recommended starting interval is **20-25 seconds**. Manual capture and any positive interval
remain available. Override downloaded asset paths with `--speech-model-path` and
`--speech-voices-path`.

Speech engines:

- `auto` (default when `--speech` is enabled) uses Kokoro when both local assets load. On macOS it
  reports the reason on stderr and falls back to the built-in `say` engine when Kokoro is not
  ready.
- `kokoro` requires the speech extra and both local assets. Explicit selection never silently
  falls back.
- `macos` uses `/usr/bin/say` and does not require the speech extra.

Kokoro defaults to the `af_sarah` preset. Pass another installed Kokoro preset with
`--speech-voice`, or a voice listed by `say -v ?` when using `--speech-engine macos`. A speech rate
of `1.0` is Kokoro's normal speed and maps to approximately 200 words per minute for macOS speech.

After the dependencies and model assets are installed, Kokoro synthesis and playback are fully
local. The macOS fallback is also local. Existing terminal and preview descriptions remain
available if speech fails after startup.

Run `uv run camera-vision --help` for every option.

## Behavior

- Frames are JPEG-encoded in memory and sent directly to the local Ollama API. No capture image is
  written to the project directory.
- Only one model request runs at a time. If an automatic interval or Space-key capture occurs while
  Ollama is busy, that frame is skipped rather than queued. This keeps descriptions current and
  prevents an unbounded backlog.
- The preview remains responsive during inference and shows current state plus a bounded version of
  the latest result. Terminal output retains the complete description.
- Expected image-encoding and Ollama request failures are reported and the application remains
  ready for a later capture.
- Speech runs outside the camera loop. The active sentence finishes; while it plays, only the
  newest pending description is retained and older pending descriptions are discarded.
- Speech errors are reported on stderr while text output and later camera captures continue.
- Quitting prevents pending narration from starting and waits for the active sentence to finish
  before closing speech resources.
- Quitting waits for any active Ollama request up to the configured request timeout before process
  shutdown completes.

For spoken demos, prefer a concise prompt such as:

```text
Describe the most important visible objects or changes in one short sentence.
```

## Troubleshooting

### Camera cannot be opened

- Confirm camera access under **System Settings > Privacy & Security > Camera**.
- Close applications that have exclusive control of the camera.
- Try another index, such as `--camera-index 1`.
- Ensure manual modes keep the preview enabled. For no window, use `--mode interval --no-preview`.

### Camera opens but frame reads fail

Reconnect an external camera, close other camera applications, and retry. A frame-read failure is
fatal because the current stream is no longer usable; the application releases the camera before
exiting.

### Ollama is unreachable or times out

Check the service and available models:

```bash
ollama list
curl http://127.0.0.1:11434/api/tags
```

Start Ollama with `ollama serve`, verify `--host` or `OLLAMA_HOST`, and increase `--timeout` for
slower hardware.

### The model is missing

Pull the exact configured model:

```bash
ollama pull llama3.2-vision
```

If `llama3.2-vision` reports `unknown model architecture: 'mllama'`, check `ollama --version`.
This is the known [Ollama issue #16490](https://github.com/ollama/ollama/issues/16490), not a
missing model. Install Ollama 0.24.0 using the pinned macOS release link in **Setup**, fully quit
any newer Ollama server, relaunch 0.24.0, and verify the version again. Do not update Ollama to fix
this specific error.

If you need a newer Ollama release, use a vision model supported by that release and supply it with
`--model` instead of using the default.

### Analysis is slower than the interval

Skipped captures are expected backpressure. Increase `--interval` or choose a smaller local vision
model. The application intentionally does not process stale queued frames.

### Speech does not start

- For Kokoro, run `uv sync --extra speech` and confirm both asset files exist at the paths shown by
  `uv run camera-vision --help`.
- Use `--speech-engine kokoro` to turn missing dependencies or assets into an explicit startup
  error instead of automatic macOS fallback.
- For system speech, confirm `/usr/bin/say` exists and list available voices with `say -v ?`.
- Do not pass a Kokoro preset name to the macOS engine; voice names are engine-specific.
- Check **System Settings > Sound > Output** for the selected output device and volume.

Speech synthesis or playback errors after startup are reported on stderr without stopping camera
analysis. If audio hardware remains unavailable, omit `--speech` and use text output or the
existing stdout pipeline.

## Development

The project uses OpenSpec for proposal-driven changes. The active change and its requirements,
design, and implementation checklist are under `openspec/changes/improve-camera-vision/`.

```bash
uv sync --dev
uv run ruff check .
uv run pytest
openspec validate improve-camera-vision --strict
```
