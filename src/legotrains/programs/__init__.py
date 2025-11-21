"""Program framework for LegoTrains."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from importlib.util import find_spec
from pathlib import Path
from typing import ClassVar, Dict, Iterable, Type

from ..hardware_connection import HubConnectionManager
from ..state import Event, EventBus, EventSeverity


@dataclass(frozen=True)
class ProgramMetadata:
    """Metadata describing a train program."""

    name: str
    description: str = ""


class TrainProgram:
    """Base class for custom train programs."""

    metadata: ClassVar[ProgramMetadata]

    def __init__(
        self,
        connections: HubConnectionManager,
        event_bus: EventBus | None = None,
    ) -> None:
        self._connections = connections
        self._event_bus = event_bus

    async def run(self) -> None:
        """Entry point executed when the program starts."""

        await self.on_start()
        await self.execute()
        await self.on_complete()

    async def on_start(self) -> None:
        await self.log(f"{self.metadata.name} started")

    async def on_complete(self) -> None:
        await self.log(f"{self.metadata.name} finished")

    async def execute(self) -> None:
        """User-defined logic block."""

        raise NotImplementedError

    async def set_speed(self, train_id: str, speed: int) -> bool:
        try:
            await self._connections.set_speed(train_id, speed)
            return True
        except RuntimeError as exc:
            await self.log(str(exc), severity=EventSeverity.WARNING)
            return False

    async def stop(self, train_id: str) -> None:
        try:
            await self._connections.stop(train_id)
        except RuntimeError as exc:
            await self.log(str(exc), severity=EventSeverity.WARNING)

    async def log(self, message: str, *, severity: EventSeverity = EventSeverity.INFO) -> None:
        if not self._event_bus:
            return
        await self._event_bus.publish(Event(type="program_log", message=message, severity=severity))


_REGISTRY: Dict[str, Type[TrainProgram]] = {}


def register_program(cls: Type[TrainProgram]) -> Type[TrainProgram]:
    """Decorator for registering program classes."""

    metadata = getattr(cls, "metadata", None)
    if not metadata or not metadata.name:
        raise ValueError("TrainProgram subclasses must define metadata with a non-empty name.")
    _REGISTRY[metadata.name] = cls
    return cls


def available_programs() -> Iterable[ProgramMetadata]:
    return (cls.metadata for cls in _REGISTRY.values())


def load_program(name: str, connections: HubConnectionManager, event_bus: EventBus | None = None) -> TrainProgram:
    try:
        cls = _REGISTRY[name]
    except KeyError as exc:
        raise KeyError(f"No program registered under name `{name}`.") from exc
    return cls(connections=connections, event_bus=event_bus)


def discover_programs(*modules: str) -> None:
    for module in modules:
        import_module(module)


def discover_programs_from_package(package: str) -> None:
    spec = find_spec(package)
    if spec is None:
        raise ModuleNotFoundError(f"Package `{package}` not found for program discovery.")
    import_module(package)
    if spec.submodule_search_locations:
        for location in spec.submodule_search_locations:
            for entry in Path(location).glob("*.py"):
                if entry.name == "__init__.py":
                    continue
                import_module(f"{package}.{entry.stem}")


__all__ = [
    "ProgramMetadata",
    "TrainProgram",
    "register_program",
    "available_programs",
    "load_program",
    "discover_programs",
    "discover_programs_from_package",
]
