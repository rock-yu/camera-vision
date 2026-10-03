# Proposal

## Why

The current repository is a single blocking script with hard-coded settings, temporary image
files, and no repeatable installation or test workflow. It needs a reliable local application
that can continuously preview a laptop camera, request descriptions from Ollama, and compose
those descriptions with other offline tools.

## What Changes

- Package the application as a `uv`-managed Python project with a console command and locked
  dependencies.
- Support configurable camera, Ollama host/model, prompt, request timeout, preview, and output
  behavior.
- Support both Space-key capture and configurable timed capture.
- Keep the camera preview responsive during model inference and prevent overlapping requests or
  an accumulating stale-frame queue.
- Send JPEG-encoded frames to Ollama in memory instead of using a shared temporary file.
- Display the current state and latest description in the preview.
- Provide human-readable terminal output and description-only stdout suitable for piping to an
  external text-to-speech command, with status and errors isolated on stderr.
- Add explicit camera, image encoding, Ollama connection/model, timeout, and malformed-response
  error handling.
- Add deterministic automated tests and macOS-first installation, permission, usage, and
  troubleshooting documentation.
- Remove the standalone root script in favor of one supported package entry point.

The first release does not bundle a speech model, provide a graphical settings interface, store
captured images or descriptions, stream video to the model, or promise platform-specific support
beyond macOS.

## Capabilities

### New Capabilities

- `camera-capture`: Camera selection, preview, manual and timed capture, responsive controls, and
  bounded analysis scheduling.
- `environment-description`: Local Ollama vision requests, configurable inference settings,
  in-memory image transfer, and explicit inference failure handling.
- `description-output`: Interactive terminal presentation, preview overlays, and clean stdout for
  downstream text-to-speech composition.

### Modified Capabilities

None.

## Impact

- Replaces `camera_vision.py` with an installable `src/camera_vision` package and console entry
  point.
- Adds `pyproject.toml`, `uv.lock`, Python/OpenCV/Ollama runtime dependencies, developer tooling,
  tests, and user documentation.
- Requires a locally running Ollama service, a downloaded vision model, and macOS camera
  permission for live use.
- Establishes stdout/stderr behavior as a public CLI contract for downstream processes.
