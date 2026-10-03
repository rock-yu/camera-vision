# Tasks

## 1. Project foundation

- [x] 1.1 Define the `uv`-managed Python project, console entry point, runtime/development
  dependencies, and ignore rules; verify `uv lock` and `uv sync` complete successfully
- [x] 1.2 Create the focused `src/camera_vision` package and remove the competing root script;
  verify `uv run python -c "import camera_vision"` succeeds

## 2. Configuration and output contract

- [x] 2.1 Implement validated CLI options for model, host, camera, prompt, capture mode, interval,
  preview, output mode, and timeout; verify focused parser tests cover defaults and invalid
  combinations
- [x] 2.2 Implement human and description-only reporters with strict stdout/stderr separation;
  verify output tests prove pipeline stdout contains only successful descriptions
- [x] 2.3 Document interactive, timed, headless, custom-model, and text-to-speech pipeline commands;
  verify every documented option appears in `camera-vision --help`

## 3. Local vision inference

- [x] 3.1 Implement in-memory JPEG encoding and a typed Ollama client boundary with configurable
  model, host, prompt, and timeout; verify unit tests inspect encoded bytes and request arguments
- [x] 3.2 Classify connection, timeout, missing-model, rejected-request, and malformed-response
  failures without emitting success text; verify mocked client tests cover every failure class
- [x] 3.3 Document local Ollama startup, model pull, offline boundaries, and inference
  troubleshooting; verify the setup commands are internally consistent

## 4. Camera orchestration

- [x] 4.1 Implement camera startup, frame reads, preview controls, manual/timed triggers, and
  deterministic cleanup; verify mocked orchestration tests cover startup failure, quit,
  interruption, and frame-read failure
- [x] 4.2 Run inference in one worker with one-request backpressure and result polling; verify tests
  prove busy captures are skipped, later captures recover, and preview processing remains active
- [x] 4.3 Render bounded preview status/latest-description overlays while preserving full terminal
  descriptions; verify overlay tests cover wrapping/truncation and orchestration tests cover state
  updates
- [x] 4.4 Document macOS camera permissions, camera indexes, controls, interval backpressure, and
  shutdown behavior; verify README troubleshooting covers each specified camera failure

## 5. Integration validation

- [x] 5.1 Generate and commit `uv.lock`, then run Ruff, the complete pytest suite, package import,
  module entry point, and console help smoke checks successfully
- [x] 5.2 Run `openspec validate improve-camera-vision --strict` and verify every requirement maps
  to implementation, automated coverage, documentation, or an explicitly recorded manual check
- [x] 5.3 Perform a live webcam/Ollama smoke test when the required local hardware and model are
  available; otherwise record the exact unverified environmental checks without marking this task
  complete

  Verified on this machine with camera index `0`, Ollama 0.24.0, and
  `llama3.2-vision:latest`: a camera frame was JPEG-encoded in memory and produced a model
  description successfully.
