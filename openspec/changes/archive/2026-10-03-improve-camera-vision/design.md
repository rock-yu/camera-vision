# Design

## Context

See `proposal.md` for motivation. The baseline script couples camera ownership, OpenCV UI,
temporary-file handling, Ollama requests, and presentation in one blocking loop. The application
must remain local, be usable as both an interactive preview and a terminal pipeline, and be
testable without camera or Ollama hardware.

## Goals / Non-Goals

**Goals:**

- Separate configuration, camera encoding/presentation, inference, scheduling, and output behind
  small typed boundaries.
- Preserve a responsive OpenCV event loop while a single background inference request runs.
- Make stdout/stderr behavior deterministic enough to be used as a process-level API.
- Keep installation and execution reproducible with `uv`.

**Non-Goals:**

- A long-running service API, browser UI, native macOS application, or cross-platform speech
  abstraction.
- Parallel inference, frame history, recording, or persistence.
- Automatic model download or Ollama process management.

## Decisions

### Use a `src` package with one console entry point

The project will expose `camera-vision` from a `src/camera_vision` package. Configuration/CLI,
camera helpers, Ollama integration, analysis scheduling, output, and orchestration remain focused
modules.

Alternative: keep a single script. Rejected because hardware and network boundaries would remain
difficult to test and future behavior would continue accumulating in one loop.

### Use `uv`, `pyproject.toml`, and a committed lockfile

Runtime and development dependencies will be declared once and resolved into `uv.lock`. This
provides a short setup path while preserving standard Python package metadata.

Alternative: maintain a hand-written `requirements.txt`. Rejected because it does not define the
console entry point or project metadata and tends to duplicate dependency declarations.

### Keep OpenCV work on the main thread and inference in one worker

Camera reads, preview drawing, and keyboard events stay in the main loop. A single-worker executor
runs Ollama requests. The scheduler does not accept another frame until the current result has
been polled, so stale frames cannot accumulate.

Alternative: queue every timed frame. Rejected because inference can be slower than capture and
would produce increasingly outdated environmental descriptions while consuming memory.

Alternative: run all OpenCV work in a background thread. Rejected because desktop UI event loops
are more reliable on the main thread, especially on macOS.

### Encode frames before crossing the worker boundary

The accepted frame is JPEG-encoded into immutable bytes in the camera loop and those bytes are
passed to Ollama. No shared temporary path or mutable frame is exposed to the worker.

Alternative: save each image to disk. Rejected because cleanup and filename collisions complicate
failures and create unnecessary local artifacts.

### Treat stdout as a selectable external contract

Human mode can add visual delimiters to stdout. Description-only mode emits only successful
descriptions there; all operational communication goes to stderr. Preview rendering uses a copy
and only stores the latest successful text.

Alternative: add built-in text-to-speech. Rejected because speech engine/model selection has
different dependencies and platform constraints; a clean stdout boundary supports any local TTS
tool without coupling it to camera inference.

### Recover only from classified request and encoding failures

Known Ollama transport/model/response errors and frame-encoding failures are reported and return
the app to a ready state. Unclassified programming errors are not swallowed; cleanup still occurs
through `finally` blocks.

Alternative: catch every exception and continue. Rejected because it can hide broken invariants
and produce misleading success-shaped behavior.

## Risks / Trade-offs

- **A worker shutdown may wait for an active Ollama request** → Apply a configurable positive
  request timeout and document that quitting can wait for the active request boundary.
- **OpenCV camera indexes and permission messages vary by machine** → Report the selected index,
  document macOS privacy settings, and avoid claiming a camera exists before opening it.
- **Long descriptions do not fit a preview window** → Wrap and bound overlay lines while preserving
  full terminal output.
- **Timed intervals shorter than inference duration skip captures** → Make backpressure explicit in
  status and documentation; freshness is preferred over processing every frame.
- **Ollama client response types can differ across supported versions** → Normalize both typed
  response objects and mapping-shaped responses behind the inference boundary.

## Migration Plan

1. Add package metadata and the `src/camera_vision` modules.
2. Replace the root script with the `camera-vision` console command.
3. Add mocked tests for behavior at each hardware/network boundary.
4. Add setup and migration examples to the README.
5. Validate OpenSpec artifacts, dependency resolution, lint, tests, package import, and CLI help.

Rollback consists of restoring the prior standalone script; no user data or persisted schema is
migrated.
