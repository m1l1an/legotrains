import asyncio
from bleak import BleakScanner

async def scan():
    devices = await BleakScanner.discover()
    for d in devices:
        print(d)

if __name__ == "__main__":
    asyncio.run(scan())
