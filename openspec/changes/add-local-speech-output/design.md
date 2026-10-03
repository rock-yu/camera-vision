# Design

## Context

See `proposal.md` for motivation. The current application publishes each completed vision result
through `Reporter` on the main camera loop. Vision inference already runs in one background worker,
and the observed `llama3.2-vision` latency is approximately 17-19 seconds. Speech must therefore
improve the demo without coupling playback to the camera loop or expanding scope into vision-model
optimization.

## Goals / Non-Goals

**Goals:**

- Add local narration behind a small engine interface that can be mocked in tests.
- Preserve the existing stdout/stderr contract and camera responsiveness.
- Keep only fresh pending speech without interrupting an utterance in progress.
- Provide a low-friction macOS demo when neural model assets are not yet installed.

**Non-Goals:**

- Streaming partial model tokens or audio, voice cloning, semantic scene-change detection, or
  synchronized captions.
- Replacing `llama3.2-vision`, changing its default prompt globally, or guaranteeing a strict
  end-to-end latency.
- Generalizing system-speech fallback to Linux or Windows in this change.

## Decisions

### Introduce a speech engine protocol and controller

A speech engine accepts text and performs synthesis/playback. A separate controller owns one worker
thread, the active utterance, and a single replaceable pending text slot. Application orchestration
submits a successful description after publishing existing text output.

Alternative: call speech directly from `Reporter`. Rejected because output formatting should not
own slow audio work and synchronous playback would block camera controls.

Alternative: pipe the existing description-only stdout internally. Rejected because subprocess
composition already remains available to users, while built-in speech needs typed lifecycle,
configuration, and error reporting.

### Prefer Kokoro ONNX for neural speech

Use `kokoro-onnx` with local model and voice assets plus a direct local audio playback dependency.
The runtime supports the project's Python version, offers preset voices, and is lightweight enough
for the target Apple Silicon machine. Model assets remain outside Git and use documented default
cache paths with CLI overrides.

Alternative: MLX Audio. Deferred because it adds a broader model/runtime surface than this demo
needs.

Alternative: use only macOS `say`. Retained as fallback, but not the primary engine because the
requested experience calls for a local TTS model.

### Make engine selection explicit and observable

Speech is disabled unless requested. Engine values are `auto`, `kokoro`, and `macos`. `auto`
attempts Kokoro and reports a fallback to `/usr/bin/say` when local model assets cannot load.
Explicit `kokoro` selection fails before camera startup with setup guidance rather than silently
changing engines. Explicit `macos` uses argument-vector subprocess invocation without a shell.

Alternative: always fall back after any runtime failure. Rejected because synthesis failures can
indicate a broken engine and silent fallback would make behavior difficult to understand.

### Preserve freshness with one replaceable pending utterance

The active utterance is allowed to finish. While it plays, the controller stores at most one
pending description; each newer description replaces that slot. Shutdown prevents pending speech
from starting and closes the engine after the active call returns.

Alternative: queue every description. Rejected because narration could lag behind the visual
environment.

Alternative: interrupt current audio. Rejected for the first release because abrupt sentence cuts
reduce demo quality and require backend-specific cancellation.

### Keep speech settings independent from vision cadence

Add speech enablement, engine, voice, rate, and asset-path options without silently changing the
existing capture interval. Documentation recommends 20-25 seconds for the measured model latency,
but users retain manual capture and explicit interval control.

Alternative: automatically override `--interval` when speech is enabled. Rejected because hidden
configuration changes make the CLI harder to reason about.

### Treat post-start speech errors as recoverable

The controller returns or exposes classified failures for the camera loop to report on stderr.
Text output remains the source of truth and later captures continue. Initialization of an explicitly
selected engine is a startup requirement; failure there exits before acquiring the camera.

## Risks / Trade-offs

- **Kokoro model and voice assets are hundreds of megabytes and not package data** -> Keep them out
  of Git, use stable cache defaults and overrides, and document explicit download/checksum steps.
- **Audio-library installation can vary by macOS/Python release** -> Isolate playback behind the
  engine boundary and retain the built-in system-speech fallback for the demo.
- **An active utterance can delay shutdown** -> Keep descriptions concise, prevent pending speech
  from starting during shutdown, and document that the active sentence may finish.
- **Long vision descriptions produce long narration** -> Recommend a short demo prompt and bound
  the speech controller to fresh results; do not add semantic summarization in this change.
- **Automatic fallback can hide missing neural assets** -> Always report the fallback and reason on
  stderr; never use it for explicit `kokoro` selection.

## Migration Plan

1. Add optional speech dependencies and ignore/cache guidance without committing model assets.
2. Add speech configuration, engine protocol, Kokoro and macOS implementations, and controller.
3. Wire successful descriptions into the controller while preserving existing output.
4. Add deterministic tests using fake speech engines and subprocess/audio boundaries.
5. Add setup, demo, fallback, asset, and troubleshooting documentation.
6. Validate automated checks, then perform separate neural and system-speech speaker smoke tests.

Rollback removes the speech modules/options and optional dependencies; existing camera and text
output behavior remains unchanged because speech is opt-in.
