# Spec Delta

## Purpose

Defines how descriptions, operational status, errors, and preview information are presented to
interactive users and downstream local processes.

## ADDED Requirements

### Requirement: Human-readable terminal output
The default output mode SHALL present completed descriptions with clear visual delimiters while
operational status and errors remain distinguishable.

#### Scenario: Interactive description completes
- **WHEN** inference succeeds in human-readable output mode
- **THEN** stdout displays the full description between readable delimiters

### Requirement: Composable description-only output
Description-only mode SHALL write each successful model description as one whitespace-normalized
line on stdout. All startup messages, controls, status updates, and errors SHALL be written to
stderr.

#### Scenario: Output is piped to speech tooling
- **WHEN** the application runs with description-only output and inference succeeds
- **THEN** stdout contains the complete description as one whitespace-normalized line
- **AND** contains no headers, progress messages, controls, or errors

#### Scenario: Inference fails in description-only mode
- **WHEN** a request fails before producing a valid description
- **THEN** stdout receives no success-shaped text for that request
- **AND** stderr receives the error

### Requirement: Preview status and latest description
When preview is enabled, the application SHALL display its current analysis state and a
readable, bounded rendering of the latest successful description without altering the full
terminal output.

#### Scenario: Analysis is running
- **WHEN** a frame has been submitted and inference has not completed
- **THEN** the preview indicates that analysis is in progress

#### Scenario: Description exceeds preview space
- **WHEN** a successful description is too long for the bounded preview overlay
- **THEN** the preview displays a wrapped and truncated representation
- **AND** terminal output retains the complete description

### Requirement: Headless timed operation
The application SHALL support timed capture with the preview disabled and SHALL provide an
interrupt-based quit path suitable for terminal pipelines.

#### Scenario: Timed pipeline runs without a window
- **WHEN** the user selects timed capture, disables preview, and uses description-only output
- **THEN** descriptions are emitted to stdout without opening a preview window
- **AND** Ctrl-C shuts down the application cleanly
