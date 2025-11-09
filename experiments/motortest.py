from pylgbst.hub import MoveHub
from pylgbst import get_connection_bleak

import time
import logging

# Set logging level to INFO so you can see when the hub connects and disconnects
logging.basicConfig(level=logging.INFO)

# --- Configuration ---
# IMPORTANT: Replace the name below with the exact name you saw during the Bleak scan.
# Common names are 'LEGO Train Hub', 'LEGO Hub', or 'LEGO Move Hub'.
TARGET_HUB_NAME = "FreightTrain"


def run_train_motor():
    """
    Connects to the specified LEGO Hub, runs the motor on Port A, and disconnects.
    """
    hub = None
    try:
        print(f"Connecting to Hub named '{TARGET_HUB_NAME}'...")

        # This function scans and connects to the first hub it finds matching the name
        # If no name is provided, it connects to the first available hub.
        # conn = get_connection_auto(TARGET_HUB_NAME)
        conn = get_connection_bleak(hub_mac="90:84:2B:CB:94:90")
        hub = MoveHub(conn)

        print("✅ Connection successful!")

        # Access the motor on Port A (this is an EncodedMotor object in pylgbst)
        motor = hub.motor_A

        if motor:
            print("🚂 Starting motor ...")

            # set_speed starts the motor
            motor.power(0.8)
            time.sleep(2)
            motor.stop()

        else:
            print("⚠️ Warning: No motor detected or configured for Port A.")

    except Exception as e:
        print(f"\n❌ An error occurred during connection or operation: {e}")
        print(
            "Troubleshooting: Is the hub turned on and advertising? Did you check the hub name?"
        )
    finally:
        if hub:
            print("Disconnecting from the hub.")
            hub.disconnect()
            print("Connection closed.")


if __name__ == "__main__":
    run_train_motor()
