# Spec Delta

## Purpose

Defines local vision inference behavior that turns a captured camera frame into an environmental
description through a configurable Ollama service.

## ADDED Requirements

### Requirement: Configurable local vision request
The application SHALL send each accepted frame and configured prompt to the configured Ollama
host and vision model, defaulting to `llama3.2-vision` and Ollama's local host behavior.

#### Scenario: Default description request
- **WHEN** a capture is accepted with no model, host, or prompt overrides
- **THEN** the application requests a description from local Ollama using `llama3.2-vision`
- **AND** asks for a detailed description of the environment

#### Scenario: User overrides inference settings
- **WHEN** the user provides a model, host, prompt, or positive timeout override
- **THEN** every subsequent request uses those configured values

### Requirement: In-memory frame transfer
The application SHALL JPEG-encode accepted camera frames in memory and SHALL provide those bytes
directly to Ollama without creating a persistent or shared capture file.

#### Scenario: Frame is accepted for analysis
- **WHEN** the application submits a camera frame
- **THEN** it sends JPEG bytes with the Ollama request
- **AND** no capture image is written to the working directory

#### Scenario: Frame encoding fails
- **WHEN** the current frame cannot be JPEG-encoded
- **THEN** the application reports the encoding failure on stderr
- **AND** remains ready for a later capture

### Requirement: Valid model description
The application SHALL treat only a non-empty textual model response as a successful description.

#### Scenario: Ollama returns text
- **WHEN** Ollama returns a non-empty message content value
- **THEN** the application publishes the trimmed text as the completed description

#### Scenario: Ollama response is malformed
- **WHEN** Ollama returns no textual message content or only whitespace
- **THEN** the application reports a malformed-response error
- **AND** does not publish a successful description

### Requirement: Actionable inference failures
The application SHALL distinguish unreachable or timed-out Ollama services, unavailable models,
and rejected requests, and SHALL remain available for later captures after expected request
failures.

#### Scenario: Ollama cannot be reached
- **WHEN** the configured Ollama service refuses the connection or times out
- **THEN** the application reports server startup or timeout guidance on stderr

#### Scenario: Model is unavailable
- **WHEN** Ollama reports that the configured model does not exist
- **THEN** the application reports the model name and the corresponding `ollama pull` command

#### Scenario: A request fails and a later request succeeds
- **WHEN** one accepted request produces an expected inference error
- **THEN** the application returns to a ready state
- **AND** permits a later capture to be analyzed
