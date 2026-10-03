# Camera Vision

Describe your laptop camera feed with a vision model running locally through
[Ollama](https://ollama.com/). Camera frames, prompts, and model responses stay on your machine
when Ollama and any downstream speech tool are local.

## Requirements

- macOS with camera access enabled for your terminal application
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [Ollama](https://ollama.com/download)
- A local Ollama vision model; the default is `llama3.2-vision`

The Python code uses portable OpenCV APIs, but this first release documents and targets macOS.

## Setup

Install and start Ollama, then download the default vision model:

```bash
brew install ollama
ollama serve
```

In another terminal:

```bash
ollama pull llama3.2-vision
uv sync
```

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
- Quitting waits for any active Ollama request up to the configured request timeout before process
  shutdown completes.

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

If Ollama reports an unknown model architecture or terminates while loading a freshly pulled
model, update the Ollama application/runtime and retry. The model files can be present even when
the installed runtime is too old to load their architecture.

### Analysis is slower than the interval

Skipped captures are expected backpressure. Increase `--interval` or choose a smaller local vision
model. The application intentionally does not process stale queued frames.

## Development

The project uses OpenSpec for proposal-driven changes. The active change and its requirements,
design, and implementation checklist are under `openspec/changes/improve-camera-vision/`.

```bash
uv sync --dev
uv run ruff check .
uv run pytest
openspec validate improve-camera-vision --strict
```
