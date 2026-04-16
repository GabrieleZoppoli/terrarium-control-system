import asyncio
import json
import os
import sys
from meross_iot.http_api import MerossHttpClient
from meross_iot.manager import MerossManager

EMAIL = os.environ.get("MEROSS_EMAIL", "your_email@example.com")
PASSWORD = os.environ.get("MEROSS_PASSWORD", "your_password")
PLUG_ID = os.environ.get("MEROSS_PLUG_ID", "your_plug_name")

async def control_plug_or_fetch_energy(action):
    manager = None
    http_api_client = None
    try:
        # Initialize Meross Client
        api_base_url = "https://iotx-eu.meross.com"
        http_api_client = await MerossHttpClient.async_from_user_password(email=EMAIL, password=PASSWORD, api_base_url=api_base_url)
        manager = MerossManager(http_client=http_api_client)
        await manager.async_init()

        # Discover devices
        await manager.async_device_discovery()
        plug = next((dev for dev in manager.find_devices() if dev.name == PLUG_ID), None)

        if plug is None:
            raise Exception(f"No plug named '{PLUG_ID}' found.")

        # Update plug status
        await plug.async_update()

        result = ""
        if action == "on":
            await plug.async_turn_on(channel=0)
            result = f"Turned on {PLUG_ID}"
        elif action == "off":
            await plug.async_turn_off(channel=0)
            result = f"Turned off {PLUG_ID}"
        elif action == "get_energy":
            if hasattr(plug, 'async_get_instant_metrics'):
                electricity = await plug.async_get_instant_metrics()
                result = f"Instant Power Consumption: {electricity.power} W"
            else:
                result = "This device does not support energy consumption reading."
        else:
            result = "Invalid action. Specify 'on', 'off', or 'get_energy'."

        return json.dumps({"result": result})

    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        if manager:
            manager.close()
        if http_api_client:
            await http_api_client.async_logout()

# Command-line argument execution
if __name__ == "__main__":
    if len(sys.argv) > 1:
        action = sys.argv[1]
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(control_plug_or_fetch_energy(action))
        print(result)
    else:
        print(json.dumps({"error": "No action specified"}))

