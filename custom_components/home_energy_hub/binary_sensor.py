"""Binary sensors for Home Energy Hub (V3 PIC/SFA bits)."""

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .integrations.seplos_v3.vendor_spec import PIC_BITS, SFA_BITS

_LOGGER = logging.getLogger(__name__)


class SeplosV3BinarySensor(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator, kind, index, name, battery_address, prefix, entry_id):
        super().__init__(coordinator)
        self._kind = kind
        self._index = index
        self._attr_has_entity_name = False
        self._attr_name = f"{prefix} {battery_address} {name}"
        self._attr_unique_id = (
            f"home_energy_hub_v3_{entry_id}_{kind}_{battery_address}_{index}_{name}"
        )
        settings = kind == "sfa"
        suffix = "_settings" if settings else ""
        self._attr_device_info = DeviceInfo(
            identifiers={("home_energy_hub", f"seplos_v3_{entry_id}{suffix}")},
            name=f"{prefix} Settings" if settings else f"{prefix}",
            manufacturer="Seplos",
            model="V3 Settings" if settings else "V3 BMS",
            sw_version="Unknown",
        )

    @property
    def is_on(self):
        key = "pic_bits" if self._kind == "pic" else "sfa_bits"
        bits = (self.coordinator.data or {}).get(key) or []
        try:
            return bool(bits[self._index])
        except IndexError:
            return False


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry,
                            async_add_entities: AddEntitiesCallback):
    if entry.data.get("integration_type") != "seplos_v3":
        return
    coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if coordinator is None:
        return
    address = entry.data.get("battery_address", "0x00")
    prefix = entry.data.get("name_prefix", "Seplos BMS V3")
    entities = []
    for index, item in enumerate(PIC_BITS):
        entities.append(SeplosV3BinarySensor(coordinator, "pic", index, item["name"], address, prefix, entry.entry_id))
    for index, item in enumerate(SFA_BITS):
        entities.append(SeplosV3BinarySensor(coordinator, "sfa", index, item["name"], address, prefix, entry.entry_id))
    async_add_entities(entities)
