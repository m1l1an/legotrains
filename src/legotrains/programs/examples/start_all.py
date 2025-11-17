"""Example program that spins both trains briefly."""

from __future__ import annotations

import asyncio

from .. import ProgramMetadata, TrainProgram, register_program


@register_program
class StartAllTrains(TrainProgram):
    metadata = ProgramMetadata(
        name="Start All Trains",
        description="Runs both trains at 20% speed for 2 seconds, then stops.",
    )

    async def execute(self) -> None:
        await self.set_speed("freight", 20)
        await self.set_speed("passenger", 20)
        await asyncio.sleep(2)
        await self.stop("freight")
        await self.stop("passenger")
