"""Shared functionality for Shelly devices"""

MQTT_TOPIC_PREFIX = "shellies"

def get_status_topic(shelly_id: str) -> str:
    """Get the status topic for a Shelly device"""
    return f"{MQTT_TOPIC_PREFIX}/{shelly_id}/color/0/status"

def get_command_topic(shelly_id: str) -> str:
    """Get the command topic for a Shelly device"""
    return f"{MQTT_TOPIC_PREFIX}/{shelly_id}/color/0/command"

def get_set_topic(shelly_id: str) -> str:
    """Get the set topic for a Shelly device"""
    return f"{MQTT_TOPIC_PREFIX}/{shelly_id}/color/0/set"

def get_power_topic(shelly_id: str) -> str:
    """Get the power consumption topic for a Shelly device"""
    return f"{MQTT_TOPIC_PREFIX}/{shelly_id}/light/0/power"

def get_energy_topic(shelly_id: str) -> str:
    """Get the energy consumption topic for a Shelly device"""
    return f"{MQTT_TOPIC_PREFIX}/{shelly_id}/light/0/energy"

def get_online_topic(shelly_id: str) -> str:
    """Get the online status topic for a Shelly device"""
    return f"{MQTT_TOPIC_PREFIX}/{shelly_id}/online"