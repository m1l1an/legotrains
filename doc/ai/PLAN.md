# LegoTrains Implementation Plan

## 1. Guiding Principles
- Every new module must be fully type-annotated; enable `from __future__ import annotations` and fail CI on `mypy` (future addition).
- Unit tests accompany each feature; prefer pytest with asyncio fixtures, plus Textual `Pilot` for UI interactions.
- Keep BLE dependencies behind interfaces so logic can be tested without hardware.

## 2. Milestones & Tasks

### Milestone A – Platform Foundations
1. **Task A1: Configuration Loader**
   - Implement `legotrains.config` to read env vars / YAML for hub IDs and BLE options.
   - Provide dataclasses for settings + validation (hub MAC optional; when present it overrides hub name for matching).
   - *Tests*: unit tests covering env overrides, invalid config, and default fallbacks.
2. **Task A2: State Store & Events**
   - Create `StateStore`, `TrainState`, `HubState`, and `Event` dataclasses.
   - Implement async-safe publish/subscribe helpers.
   - *Tests*: concurrency-safe mutation tests, snapshot serialization, event ordering.
3. **Task A3: Logging & Telemetry**
   - Centralize structured logging with standard format; integrate with event log.
   - *Tests*: verify log entries mirrored into event stream.

### Milestone B – Hardware Layer
4. **Task B1: Hub Registry**
   - Track known trains, desired MACs, and states; expose query/update API.
   - *Tests*: registry CRUD and state transitions.
5. **Task B2: BLE Scanner Service**
   - Wrap pylgbst/Bleak discovery into asyncio task, pushing sightings to event bus.
   - *Tests*: mock Bleak scanner to verify filtering and retry scheduling.
6. **Task B3: Connection Manager & Session**
   - Manage connect/disconnect loops, instantiate pylgbst hubs, provide `set_speed`, `stop`, `play_sound`.
   - *Tests*: use fake adapter to ensure command queueing and error retries.

### Milestone C – Control & Programs
7. **Task C1: Input Mapping**
   - Map PRD key bindings to semantic commands; debounce repeated presses.
   - *Tests*: key → command translation, repeated key throttling.
8. **Task C2: TrainProgram Base & Loader**
   - Define abstract base class with metadata, event/log helpers, cancellation hooks.
   - Auto-discover programs from `programs/` or entry points.
   - *Tests*: dummy program registration, lifecycle events, error propagation.
9. **Task C3: Command Handlers**
   - Translate input/program intents into state mutations + hardware calls.
   - *Tests*: command pipeline ensures state + hardware invocation order; uses mocks for adapters.

### Milestone D – Textual UI
10. **Task D1: Layout & Widgets**
    - Implement panels for trains, program list, and log footer per PRD mock.
    - *Tests*: Textual Pilot snapshot tests for layout and indicator rendering.
11. **Task D2: UI–Service Wiring**
    - Subscribe UI to StateStore updates; display connection states and metrics.
    - *Tests*: simulate state updates, assert widget text updates.
12. **Task D3: Program Interaction**
    - Support arrow navigation, Enter to run program, show status toasts.
    - *Tests*: Pilot-driven keypress flows verifying correct program launch.

### Milestone E – Reliability & Tooling
13. **Task E1: Error Handling & Recovery**
    - Implement global exception hooks, reconnection strategy, safe shutdown.
    - *Tests*: simulate adapter failures, ensure retries and user feedback.
14. **Task E2: CLI & Packaging**
    - Add `legotrains.__main__`, CLI options (headless mode, log level), ensure editable install works.
    - *Tests*: CLI parsing unit tests.
15. **Task E3: Tooling & CI**
    - Configure Ruff + Black + pytest in pre-commit, add GitHub Actions.
    - *Tests*: run hooks locally; CI ensures lint/test gates.

## 3. Dependencies & Sequencing
- Milestone A unblocks everything else.
- Hardware tasks (B) can run in parallel once state store exists.
- Textual UI (D) depends on control & state layers (A+C) but can prototype earlier with mocks.
- Reliability/tooling (E) finalizes release readiness.

## 4. Deliverables Checklist
- Typed modules with docstrings and minimal comments where needed.
- Pytest coverage for control/state logic; markers for BLE integration tests.
- Manual test scripts documented in PRs until automation for hardware is available.
