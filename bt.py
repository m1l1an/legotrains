import asyncio
from bleak import BleakScanner, BLEDevice
from bleak.backends.scanner import AdvertisementData

async def scan_for_devices_corrected():
    """
    Scans for BLE devices and retrieves both device information and advertisement data.
    """
    print("🔍 Scanning for nearby BLE devices (5.0 seconds) with corrected RSSI retrieval...")
    
    # Use return_adv=True to get a dictionary of (BLEDevice, AdvertisementData) tuples
    devices_and_adv: dict[str, tuple[BLEDevice, AdvertisementData]] = \
        await BleakScanner.discover(timeout=5.0, return_adv=True)
    
    if not devices_and_adv:
        print("\nNo BLE devices found. Ensure Bluetooth is ON and devices are advertising.")
        return

    print(f"\n✅ Found {len(devices_and_adv)} device(s):")
    print("-" * 75)
    print(f"{'Name':<30} {'Address/UUID':<20} {'RSSI':<5} {'Local Name'}")
    print("-" * 75)

    for address, (device, advertisement_data) in devices_and_adv.items():
        # RSSI is now accessed via the AdvertisementData object
        rssi = advertisement_data.rssi
        name = device.name or '<Unknown>'
        
        # The 'local_name' is often the broadcasted name of the device (like 'LEGO Hub')
        local_name = advertisement_data.local_name or 'N/A'
        
        print(f"{name:<30} {address:<20} {rssi:<5} {local_name}")

# Run the main asynchronous function
if __name__ == "__main__":
    try:
        asyncio.run(scan_for_devices_corrected())
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        # Note: If you get a 'Bluetooth adapter not found' error, ensure your adapter is active.
