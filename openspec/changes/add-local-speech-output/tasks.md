# Tasks

## 1. Speech configuration and dependencies

- [x] 1.1 Add a `speech` optional dependency extra for Kokoro ONNX and local audio playback,
  update `uv.lock`, and verify base installation plus `uv sync --extra speech` both succeed
- [x] 1.2 Add validated speech enablement, engine, voice, rate, model-path, and voices-path
  configuration; verify parser tests cover defaults, supported combinations, invalid rates, and
  speech-disabled compatibility
- [x] 1.3 Document optional speech installation, local asset locations/downloads, and the
  20-25-second recommended demo interval; verify all documented CLI options appear in
  `camera-vision --help`

## 2. Local speech engines

- [x] 2.1 Define a typed speech-engine boundary and classified initialization, synthesis, and
  playback errors; verify unit tests can exercise the boundary without audio hardware
- [x] 2.2 Implement Kokoro ONNX model/voice loading, synthesis, and computer-audio playback using
  lazily imported optional dependencies; verify mocked tests cover selected voice/rate, missing
  assets, load failure, synthesis failure, and playback failure
- [x] 2.3 Implement macOS system speech with argument-vector subprocess execution and no shell;
  verify tests cover voice/rate arguments, unavailable `/usr/bin/say`, and non-zero process exits
- [x] 2.4 Implement `auto`, explicit `kokoro`, and explicit `macos` engine selection; verify tests
  prove automatic fallback is reported, explicit Kokoro never silently falls back, and unsupported
  platforms receive actionable errors
- [x] 2.5 Document engine selection, preset voices, macOS fallback behavior, offline boundaries,
  and engine troubleshooting; verify setup and fallback examples are consistent with configuration

## 3. Fresh non-blocking narration

- [x] 3.1 Implement a speech controller that runs outside the camera loop, finishes active speech,
  retains one pending description, and replaces it with newer text; verify deterministic
  concurrency tests cover idle submit, replacement, failure recovery, and shutdown
- [x] 3.2 Initialize speech before camera acquisition and submit only successful descriptions
  after existing terminal output; verify orchestration tests cover disabled speech, enabled speech,
  vision failure, recoverable speech failure, and camera/preview responsiveness
- [x] 3.3 Preserve description-only stdout while routing speech state and errors to stderr; verify
  combined output tests contain no speech messages on stdout
- [x] 3.4 Close speech resources during normal quit, interruption, and fatal camera failure without
  starting pending utterances; verify lifecycle tests cover each shutdown path
- [x] 3.5 Document the narration lifecycle, newest-pending policy, active-sentence shutdown
  behavior, and concise demo prompt; verify README behavior matches the speech-output scenarios

## 4. Integration validation

- [x] 4.1 Run lockfile, Ruff format/lint, complete pytest, package import, base CLI, and speech-extra
  CLI checks successfully
- [x] 4.2 Run `openspec validate add-local-speech-output --strict` and verify every speech-output
  scenario maps to implementation, tests, documentation, or a named manual check
- [x] 4.3 Perform a manual macOS system-speech smoke test through the computer speakers and record
  the selected voice/rate and observed result

  Verified with voice `Samantha` at rate `1.0` (approximately 200 WPM); `/usr/bin/say` completed
  speaker playback successfully.
- [x] 4.4 Install local Kokoro assets, perform an end-to-end camera-to-Kokoro speaker smoke test,
  and record model/voice paths, selected voice/rate, and observed result

  Verified with model `~/.cache/camera-vision/kokoro-v1.0.onnx`, voices
  `~/.cache/camera-vision/voices-v1.0.bin`, voice `af_sarah`, and rate `1.0`. Camera capture,
  `llama3.2-vision`, Kokoro synthesis, and speaker playback completed successfully; observed
  timings were 31.48 seconds for vision and 11.60 seconds for speech.
