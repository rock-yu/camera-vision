# Spec Delta

## Purpose

Defines how users select, preview, and capture a local camera while analysis remains bounded,
responsive, and safe to stop.

## ADDED Requirements

### Requirement: Camera selection and startup
The application SHALL open the configured non-negative camera index and SHALL fail with an
actionable error and non-zero exit status when that camera cannot be opened.

#### Scenario: Default camera opens
- **WHEN** the user starts the application without a camera override
- **THEN** the application opens camera index `0` and begins reading frames

#### Scenario: Selected camera is unavailable
- **WHEN** the configured camera index cannot be opened
- **THEN** the application reports the index and camera-permission guidance on stderr
- **AND** exits without starting analysis

### Requirement: Manual and timed capture modes
The application SHALL support manual capture, timed capture, and a combined mode. Manual capture
SHALL require an enabled preview, and timed capture SHALL use a positive configurable interval.

#### Scenario: User requests a manual description
- **WHEN** manual capture is enabled and the user presses Space in the preview
- **THEN** the current frame is submitted for description

#### Scenario: Timed capture becomes due
- **WHEN** timed capture is enabled and its interval elapses
- **THEN** the current frame is submitted for description without keyboard input

#### Scenario: Invalid capture configuration
- **WHEN** the user selects manual capture without a preview or provides a non-positive interval
- **THEN** the command rejects the configuration before opening a camera

### Requirement: Bounded responsive analysis
The application SHALL keep camera controls responsive while model inference runs and SHALL allow
at most one inference request in flight. A capture due while busy SHALL be skipped rather than
queued for later processing.

#### Scenario: Model is still processing
- **WHEN** a manual or timed capture is requested while another request is in flight
- **THEN** no second request is queued
- **AND** the preview continues updating

#### Scenario: Analysis completes
- **WHEN** the in-flight inference returns
- **THEN** the application makes the result available
- **AND** accepts a subsequent capture request

### Requirement: Camera controls and cleanup
The preview SHALL provide quit controls, and the application SHALL release the camera, analysis
worker, and preview windows on normal quit, interruption, startup failure, or frame-read failure.

#### Scenario: User quits from the preview
- **WHEN** the user presses Q, Shift-Q, or Escape
- **THEN** the application exits successfully and releases owned resources

#### Scenario: Camera frame read fails
- **WHEN** an opened camera does not return a frame
- **THEN** the application reports the failure on stderr
- **AND** exits non-zero after releasing owned resources
