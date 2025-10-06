"""Data coordinator for GEO IHD."""

from datetime import datetime, timedelta
import logging
from typing import Any, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api_client import GeoHomeAPIClient

_LOGGER = logging.getLogger(__name__)

class GeoIhdCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for GEO IHD."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._config = entry.data
        self.entry_id = entry.entry_id
        self.username = self._config.get("username")
        self._api_client: Optional[GeoHomeAPIClient] = None
        self._cache = {}
        super().__init__(
            hass, _LOGGER, name="GEO IHD", update_interval=timedelta(seconds=self._config.get("sensor_update_frequency", 30))
        )

    def _is_cache_valid(self, cache_key: str, expiration_delta: timedelta) -> bool:
        """Check if cache entry is valid."""
        cache_entry = self._cache.get(cache_key, {})
        timestamp = cache_entry.get('timestamp')
        if not timestamp:
            return False
        return datetime.now() - timestamp < expiration_delta

    def _update_cache(self, cache_key: str, data: Any) -> None:
        """Update cache entry."""
        self._cache[cache_key] = {
            'timestamp': datetime.now(),
            'data': data
        }

    def _get_cached_data(self, cache_key: str) -> Any:
        """Get cached data."""
        return self._cache.get(cache_key, {}).get('data')

    async def _get_consolidated_data(self) -> dict[str, Any]:
        """Fetch consolidated data from API with caching."""
        cache_key_token = f"token_{self.entry_id}"
        cache_key_system_id = f"system_id_{self.entry_id}"
        cache_key_periodic_data = f"periodic_data_{self.entry_id}"
        cache_key_live_data = f"live_data_{self.entry_id}"
        cache_key_device_data = f"device_data_{self.entry_id}"

        try:
            # Initialize API client
            if self._api_client is None:
                self._api_client = GeoHomeAPIClient(
                    self.username,
                    self._config.get("password"),
                    self._config.get("host", "https://api.geotogether.com")
                )

            async with self._api_client:
                # Get or cache system ID
                if not self._is_cache_valid(cache_key_system_id, timedelta(hours=1)):
                    if not self._is_cache_valid(cache_key_device_data, timedelta(hours=1)):
                        device_data = await self._api_client.get_device_data()
                        self._update_cache(cache_key_device_data, device_data)
                    else:
                        device_data = self._get_cached_data(cache_key_device_data)

                    system_id = device_data["systemRoles"][0]["systemId"]
                    self._update_cache(cache_key_system_id, system_id)
                else:
                    system_id = self._get_cached_data(cache_key_system_id)

                # Get periodic data
                if not self._is_cache_valid(cache_key_periodic_data, timedelta(minutes=10)):
                    periodic_meter_data = await self._api_client.get_periodic_meter_data(system_id)
                    self._update_cache(cache_key_periodic_data, periodic_meter_data)
                else:
                    periodic_meter_data = self._get_cached_data(cache_key_periodic_data)

                # Get live data
                if not self._is_cache_valid(cache_key_live_data, timedelta(seconds=30)):
                    live_meter_data = await self._api_client.get_live_meter_data(system_id)
                    self._update_cache(cache_key_live_data, live_meter_data)
                else:
                    live_meter_data = self._get_cached_data(cache_key_live_data)

                # Get device data if not cached
                if not self._is_cache_valid(cache_key_device_data, timedelta(hours=1)):
                    device_data = await self._api_client.get_device_data()
                    self._update_cache(cache_key_device_data, device_data)
                else:
                    device_data = self._get_cached_data(cache_key_device_data)

            return {
                'PeriodicMeterData': periodic_meter_data,
                'LiveMeterData': live_meter_data,
                'DeviceData': device_data
            }

        except Exception as e:
            # Invalidate cache on failure
            for key in [cache_key_token, cache_key_system_id, cache_key_periodic_data, cache_key_live_data, cache_key_device_data]:
                self._cache.pop(key, None)
            raise UpdateFailed(f"Failed to fetch GEO IHD data: {e}")

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data and build sensors."""
        try:
            data = await self._get_consolidated_data()
            sensors = {}
            # Build sensors dict
            sensors = {
                'electricity_total_consumption': {
                    'state': data['PeriodicMeterData']['totalConsumptionList'][0]['totalConsumption'],
                    'name': "Geo IHD - Electricity Total Consumption",
                    'unique_id': f"geo_ihd_electricity_total_consumption_{self.entry_id}",
                    'unit_of_measurement': "kWh",
                    'icon': "",
                    'device_class': "energy",
                    'state_class': "total_increasing",
                    'attributes': {},
                },
                'gas_total_consumption': {
                    'state': data['PeriodicMeterData']['totalConsumptionList'][1]['totalConsumption'] / 1000,
                    'name': "Geo IHD - Gas Total Consumption",
                    'unique_id': f"geo_ihd_gas_total_consumption_{self.entry_id}",
                    'unit_of_measurement': "m³",
                    'icon': "",
                    'device_class': "gas",
                    'state_class': "total_increasing",
                    'attributes': {},
                },
                'electricity_supply_status': {
                    'state': data['PeriodicMeterData']['supplyStatusList'][0]['supplyStatus'],
                    'name': "Geo IHD - Electricity Supply Status",
                    'unique_id': f"geo_ihd_electricity_supply_status_{self.entry_id}",
                    'unit_of_measurement': "",
                    'icon': "",
                    'device_class': "",
                    'state_class': "",
                    'attributes': {},
                },
                'gas_supply_status': {
                    'state': data['PeriodicMeterData']['supplyStatusList'][1]['supplyStatus'],
                    'name': "Geo IHD - Gas Supply Status",
                    'unique_id': f"geo_ihd_gas_supply_status_{self.entry_id}",
                    'unit_of_measurement': "",
                    'icon': "",
                    'device_class': "",
                    'state_class': "",
                    'attributes': {},
                },
                'electricity_bill_to_date': {
                    'state': data['PeriodicMeterData']['billToDateList'][0]['billToDate'] / 100,
                    'name': "Geo IHD - Electricity Bill To Date",
                    'unique_id': f"geo_ihd_electricity_bill_to_date_{self.entry_id}",
                    'unit_of_measurement': "GBP",
                    'icon': "",
                    'device_class': "monetary",
                    'state_class': "total_increasing",
                    'attributes': {},
                },
                'gas_bill_to_date': {
                    'state': data['PeriodicMeterData']['billToDateList'][1]['billToDate'] / 100,
                    'name': "Geo IHD - Gas Bill To Date",
                    'unique_id': f"geo_ihd_gas_bill_to_date_{self.entry_id}",
                    'unit_of_measurement': "GBP",
                    'icon': "",
                    'device_class': "monetary",
                    'state_class': "total_increasing",
                    'attributes': {},
                },
                'electricity_active_tariff_price': {
                    'state': data['PeriodicMeterData']['activeTariffList'][0]['activeTariffPrice'] / 100,
                    'name': "Geo IHD - Electricity Active Tariff Price",
                    'unique_id': f"geo_ihd_electricity_active_tariff_price_{self.entry_id}",
                    'unit_of_measurement': "GBP/kWh",
                    'icon': "",
                    'device_class': "",
                    'state_class': "",
                    'attributes': {},
                },
                'gas_active_tariff_price': {
                    'state': data['PeriodicMeterData']['activeTariffList'][1]['activeTariffPrice'] / 100,
                    'name': "Geo IHD - Gas Active Tariff Price",
                    'unique_id': f"geo_ihd_gas_active_tariff_price_{self.entry_id}",
                    'unit_of_measurement': "GBP/kWh",
                    'icon': "",
                    'device_class': "",
                    'state_class': "",
                    'attributes': {},
                },
                'electricity_cost_day': {
                    'state': data['PeriodicMeterData']['currentCostsElec'][0]['costAmount'] / 100,
                    'name': "Geo IHD - Electricity Cost (Day)",
                    'unique_id': f"geo_ihd_electricity_cost_day_{self.entry_id}",
                    'unit_of_measurement': "GBP",
                    'icon': "",
                    'device_class': "monetary",
                    'state_class': "measurement",
                    'attributes': {},
                },
                'electricity_cost_week': {
                    'state': data['PeriodicMeterData']['currentCostsElec'][1]['costAmount'] / 100,
                    'name': "Geo IHD - Electricity Cost (Week)",
                    'unique_id': f"geo_ihd_electricity_cost_week_{self.entry_id}",
                    'unit_of_measurement': "GBP",
                    'icon': "",
                    'device_class': "monetary",
                    'state_class': "measurement",
                    'attributes': {},
                },
                'electricity_cost_month': {
                    'state': data['PeriodicMeterData']['currentCostsElec'][2]['costAmount'] / 100,
                    'name': "Geo IHD - Electricity Cost (Month)",
                    'unique_id': f"geo_ihd_electricity_cost_month_{self.entry_id}",
                    'unit_of_measurement': "GBP",
                    'icon': "",
                    'device_class': "monetary",
                    'state_class': "measurement",
                    'attributes': {},
                },
                'gas_cost_day': {
                    'state': data['PeriodicMeterData']['currentCostsGas'][0]['costAmount'] / 100,
                    'name': "Geo IHD - Gas Cost (Day)",
                    'unique_id': f"geo_ihd_gas_cost_day_{self.entry_id}",
                    'unit_of_measurement': "GBP",
                    'icon': "",
                    'device_class': "monetary",
                    'state_class': "measurement",
                    'attributes': {},
                },
                'gas_cost_week': {
                    'state': data['PeriodicMeterData']['currentCostsGas'][1]['costAmount'] / 100,
                    'name': "Geo IHD - Gas Cost (Week)",
                    'unique_id': f"geo_ihd_gas_cost_week_{self.entry_id}",
                    'unit_of_measurement': "GBP",
                    'icon': "",
                    'device_class': "monetary",
                    'state_class': "measurement",
                    'attributes': {},
                },
                'gas_cost_month': {
                    'state': data['PeriodicMeterData']['currentCostsGas'][2]['costAmount'] / 100,
                    'name': "Geo IHD - Gas Cost (Month)",
                    'unique_id': f"geo_ihd_gas_cost_month_{self.entry_id}",
                    'unit_of_measurement': "GBP",
                    'icon': "",
                    'device_class': "monetary",
                    'state_class': "measurement",
                    'attributes': {},
                },
                'live_electricity_usage': {
                    'state': data['LiveMeterData']['power'][0]['watts'],
                    'name': "Geo IHD - Live Electricity Usage",
                    'unique_id': f"geo_ihd_live_electricity_usage_{self.entry_id}",
                    'unit_of_measurement': "W",
                    'icon': "",
                    'device_class': "power",
                    'state_class': "measurement",
                    'attributes': {},
                },
                'live_gas_usage': {
                    'state': data['LiveMeterData']['power'][1]['watts'],
                    'name': "Geo IHD - Live Gas Usage",
                    'unique_id': f"geo_ihd_live_gas_usage_{self.entry_id}",
                    'unit_of_measurement': "W",
                    'icon': "",
                    'device_class': "power",
                    'state_class': "measurement",
                    'attributes': {},
                },
                'electricity_zigbee_status': {
                    'state': data['LiveMeterData']['zigbeeStatus']['electricityClusterStatus'],
                    'name': "Geo IHD - Electricity Zigbee Status",
                    'unique_id': f"geo_ihd_electricity_zigbee_status_{self.entry_id}",
                    'unit_of_measurement': "",
                    'icon': "",
                    'device_class': "",
                    'state_class': "",
                    'attributes': {},
                },
                'gas_zigbee_status': {
                    'state': data['LiveMeterData']['zigbeeStatus']['gasClusterStatus'],
                    'name': "Geo IHD - Gas Zigbee Status",
                    'unique_id': f"geo_ihd_gas_zigbee_status_{self.entry_id}",
                    'unit_of_measurement': "",
                    'icon': "",
                    'device_class': "",
                    'state_class': "",
                    'attributes': {},
                },
            }
            return sensors
        except Exception as err:
            raise UpdateFailed(f"GEO IHD update failed: {err}")