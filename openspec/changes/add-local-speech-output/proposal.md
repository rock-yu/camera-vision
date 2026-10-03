# Proposal

## Why

Camera descriptions currently require reading terminal or preview text, which limits the demo as
an ambient accessibility experience. The application should narrate successful local vision
results through the computer's speakers while preserving the existing offline workflow.

## What Changes

- Add optional built-in local text-to-speech narration for completed vision descriptions.
- Use a lightweight Kokoro ONNX preset voice as the primary local speech engine on macOS.
- Provide macOS system speech as a low-cost fallback when Kokoro assets are unavailable.
- Keep speech off by default so existing terminal, preview, and pipeline behavior remains
  compatible.
- Add configurable speech engine, voice, and rate options with actionable validation.
- Run speech outside the camera/UI loop so playback does not block capture controls or preview
  updates.
- Finish the current utterance and retain only the newest pending description, preventing stale
  speech queues during slower vision inference.
- Report speech initialization, synthesis, and playback failures on stderr without terminating
  camera analysis or emitting success-shaped speech status on stdout.
- Document an approximately 20-25 second demo cadence for the observed `llama3.2-vision` latency,
  while retaining manual and user-configured interval modes.

The first release does not replace or optimize the vision model, promise sub-five-second scene
analysis, clone voices, stream partial vision output into speech, interrupt an utterance already
playing, compare scenes semantically, or support a cross-platform audio backend beyond the
Kokoro path and macOS fallback.

## Capabilities

### New Capabilities

- `speech-output`: Local speech synthesis, audio playback, freshness policy, configuration, and
  recoverable failure behavior for completed environment descriptions.

### Modified Capabilities

None.

## Impact

- Adds a speech abstraction and asynchronous speech controller to the application runtime.
- Adds optional Kokoro ONNX/audio dependencies and local model asset setup.
- Extends CLI configuration and application orchestration without changing existing output-mode
  contracts.
- Adds mocked speech/audio tests plus a manual speaker-output smoke test.
- Updates installation, demo, fallback, voice, and troubleshooting documentation.
