"""Example program that spins both trains briefly."""

from __future__ import annotations

import asyncio

from .. import ProgramMetadata, TrainProgram, register_program


@register_program
class StopAndGo(TrainProgram):
    metadata = ProgramMetadata(
        name="Stop and Go",
        description="",
    )

    async def execute(self) -> None:
        pass
        # YOUR TASK:
        # Start the passanger train on a slow speed, let it roll for 0.5 seconds, then stop it
        # Start the freight train on a slow speed, let it roll for 0.5 seconds, then stop it
        # Repeat above 20 times (use a for loop!)

        # Hints:
        # Starting the freight train with speed 20:
        # await self.set_speed("freight", 20)
        # Starting the passenger train with speed 20:
        # await self.set_speed("passenger", 20)
        # Stopping the freight train:
        # await self.stop("freight")
        # Waiting for 1.5 seconds:
        # await asyncio.sleep(1.5)

        # DO NOT FORGET THE "pass" AT THE BEGINNING!
