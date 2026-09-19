from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import LondonPollenCoordinator
from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = LondonPollenCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    async_add_entities(
        [
            LondonPollenLevelSensor(coordinator, entry),
            LondonPollenAllergensSensor(coordinator, entry),
        ]
    )


class LondonPollenBaseSensor(CoordinatorEntity[LondonPollenCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Community integration",
            "model": "The Weather Network pollen feed",
            "configuration_url": coordinator.data.source_url,
        }


class LondonPollenLevelSensor(LondonPollenBaseSensor):
    entity_description = SensorEntityDescription(key="level", name="Level", icon="mdi:flower-pollen")

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_level"

    @property
    def native_value(self):
        return self.coordinator.data.level

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        return {
            "top_allergens": data.allergens,
            "forecast": data.forecast,
            "source_updated": data.source_updated,
            "attribution": "Forecast data displayed from The Weather Network; pollen data credited there to Aerobiology Research Laboratories.",
            "source_url": data.source_url,
        }


class LondonPollenAllergensSensor(LondonPollenBaseSensor):
    entity_description = SensorEntityDescription(key="allergens", name="Top allergens", icon="mdi:leaf")

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_allergens"

    @property
    def native_value(self):
        return ", ".join(self.coordinator.data.allergens) or "Unknown"
