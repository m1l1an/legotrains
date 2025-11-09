# LegoTrains Detailed Design

## 1. Context & Goals
- Deliver a Textual-based TUI that lets students control two predefined trains (Freight & Passenger) while encouraged to write their own programs.
- Maintain continuous BLE discovery and reconnection logic using pylgbst on top of Bleak.
- Provide a clean API for user-authored TrainProgram subclasses without requiring them to touch hardware details.
- Optimize for classroom reliability: graceful hub loss, visible status, and deterministic key bindings.

## 2. System Overview
```
+-------------------+        +-----------------+        +------------------+
| Textual Frontend  | <----> | Control Services| <----> | Hardware Drivers |
+-------------------+        +-----------------+        +------------------+
        ^                           ^                             ^
        |                           |                             |
   Train Programs             Event Bus /                 pylgbst hubs
    (student code)           State Repository           + Bleak scanner
```
- The Textual app renders panels per train, an event log, and the program list.
- Control services manage train state, schedule programs, and translate key bindings to motor commands.
- Hardware drivers encapsulate hub discovery, connections, and motor APIs.

## 3. Module Breakdown
| Module | Responsibility |
| --- | --- |
| `legotrains.main` | CLI/bootstrap; wires logging, config, and launches Textual app. |
| `legotrains.app.ui` | Textual `App`, views, widgets, key bindings, log panel. |
| `legotrains.state.models` | Data classes for Train, HubState, Program metadata; serializable for logging/tests. |
| `legotrains.hardware.registry` | Tracks known hubs, target MACs, connection status. |
| `legotrains.hardware.adapters` | Async wrappers around pylgbst devices; exposes high-level `set_speed(train_id, speed)` APIs. |
| `legotrains.control.programs` | Base `TrainProgram` + registry + loader for user scripts. |
| `legotrains.control.input` | Maps keystrokes to commands, debounces repeat presses, and publishes intent events. |
| `legotrains.services.events` | Lightweight pub/sub (asyncio Queue) to decouple UI, hardware, and programs. |

## 4. Hardware & Connectivity Flow
1. `hardware.registry` seeds `FreightTrain` and `PassengerTrain` with target hub IDs from config.
2. `hardware.adapters.Scanner` runs a Bleak scan loop (background task) and emits sightings.
3. On match, `ConnectionManager` transitions hub state DISCONNECTED → CONNECTING → CONNECTED via pylgbst API, creating a `HubSession`.
4. Motor/LED commands route through `HubSession`, which guards against stale connections and queue overload.
5. Any disconnect triggers retries and UI updates; errors surface via the event bus.

## 5. Textual UI Flow
- Layout: three columns (Freight panel, Programs, Passenger panel) + footer log, mirroring the PRD mockup.
- Panels subscribe to state updates and render status (`<Moving>`, `<Stopped>`, CONNECTING banners).
- Global key handlers (w/W/s/S/x for Freight, i/I/k/K/, for Passenger, `q` quit) dispatch intents to `control.input`.
- Program list navigated via arrow keys; hitting Enter invokes the selected `TrainProgram.run()` coroutine.

## 6. Train Programs Lifecycle
1. User program subclasses `TrainProgram` and declares metadata (name, description, requirements).
2. `control.programs.loader` auto-discovers modules under `programs/` or entry points.
3. When launched, program receives handles to both trains plus async helpers (awaitable `set_speed`, `sleep`, `log`).
4. Programs run in dedicated asyncio tasks with cancellation hooks so the UI remains responsive.

## 7. State & Event Handling
- Central `StateStore` (async-safe dataclass copy) holds latest train speeds, connection status, and active program.
- Mutations happen via command handlers emitting `StateChanged` events; UI widgets simply render snapshots.
- Event log stores recent N entries with timestamps and surfaces to the footer panel.

## 8. Testing & Tooling Strategy
- Unit-test control modules with pytest + asyncio fixtures; mocks for pylgbst sessions.
- Use Textual’s `Pilot` utility for widget interaction tests.
- Provide BLE integration tests guarded by `pytest -m "ble"` that run against real hubs in the lab.
- Lint/format via Ruff + Black; enforce via pre-commit hooks once added.

## 9. Deployment & Developer Experience
- Developers run `PYTHONPATH=src python -m legotrains.main` during early development, switching to `pip install -e .` for CLI parity.
- Provide `.env.example` for hub IDs; `legotrains.config` reads env or YAML.
- Future work: package as `textual run legotrains.app.ui:App` once ready.

## 10. Open Questions
- No hot reload needed for student programs
- No persistence needed
- No need for safety limits for now


