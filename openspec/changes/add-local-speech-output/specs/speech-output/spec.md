# Spec Delta

## Purpose

Defines optional local speech synthesis and speaker playback for completed environment
descriptions while keeping narration current, non-blocking, and recoverable.

## ADDED Requirements

### Requirement: Optional local narration
The application SHALL allow users to enable local speech for successful environment descriptions
and SHALL keep speech disabled by default to preserve existing behavior.

#### Scenario: Speech is enabled
- **WHEN** a valid environment description completes and speech is enabled
- **THEN** the application sends the complete description to the configured local speech engine
- **AND** plays the resulting speech through the computer's selected audio output

#### Scenario: Speech is disabled
- **WHEN** a valid environment description completes and speech is not enabled
- **THEN** existing terminal and preview output continue unchanged
- **AND** no speech synthesis or playback is attempted

#### Scenario: Vision analysis fails
- **WHEN** a capture produces no valid environment description
- **THEN** the application does not synthesize or play speech for that capture

### Requirement: Configurable speech experience
The application SHALL provide validated options for speech engine, preset voice, and speaking
rate, and SHALL report unsupported or invalid combinations before camera analysis begins.

#### Scenario: User selects speech settings
- **WHEN** the user enables speech with a supported engine, voice, and positive speaking rate
- **THEN** every narrated description uses those settings

#### Scenario: Speech configuration is invalid
- **WHEN** the user supplies an unsupported engine, unavailable explicit voice, or non-positive
  speaking rate
- **THEN** the command reports an actionable configuration error
- **AND** exits before opening the camera

### Requirement: Engine selection and fallback
Automatic speech-engine selection SHALL prefer the configured local neural engine and SHALL use
the macOS system speech engine only when neural model assets are unavailable, reporting the
fallback on stderr. Explicit engine selection SHALL not silently fall back.

#### Scenario: Neural speech assets are ready
- **WHEN** speech uses automatic engine selection and required local neural assets can be loaded
- **THEN** narration uses the neural speech engine

#### Scenario: Automatic selection cannot load neural assets
- **WHEN** speech uses automatic engine selection on macOS and required neural assets are missing
  or cannot be loaded
- **THEN** the application reports the reason and selected system-speech fallback on stderr
- **AND** narration remains available through the fallback

#### Scenario: Explicit neural engine is unavailable
- **WHEN** the user explicitly selects the neural engine and its required assets cannot be loaded
- **THEN** the application reports actionable asset setup guidance
- **AND** exits before opening the camera

### Requirement: Non-blocking fresh narration
Speech synthesis and playback SHALL not block camera reads, preview controls, or vision-result
handling. The application SHALL finish the current utterance, retain at most one pending
description, and replace that pending description when a newer result arrives.

#### Scenario: Description arrives while speech is idle
- **WHEN** a successful description completes and no utterance is active
- **THEN** narration begins without blocking the camera loop

#### Scenario: Multiple descriptions arrive during an utterance
- **WHEN** two or more successful descriptions complete while speech is active
- **THEN** the current utterance finishes without interruption
- **AND** only the newest pending description is narrated next

#### Scenario: User quits while speech is active
- **WHEN** the user quits or interrupts the application during narration
- **THEN** speech resources are closed along with camera and preview resources
- **AND** no additional pending utterance starts

### Requirement: Recoverable speech failures
Speech initialization, synthesis, and playback failures SHALL be reported on stderr and SHALL not
be presented as successful narration or terminate an otherwise healthy camera-analysis session,
except when an explicitly selected engine cannot initialize before startup.

#### Scenario: Synthesis or playback fails after startup
- **WHEN** an enabled speech engine fails to synthesize or play a description
- **THEN** the application reports the speech failure on stderr
- **AND** terminal and preview description output remain available
- **AND** later vision captures continue

#### Scenario: Description-only output is combined with speech
- **WHEN** speech and description-only output are both enabled
- **THEN** stdout continues to contain only successful normalized descriptions
- **AND** speech status and errors remain on stderr
