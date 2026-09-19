from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from html import unescape
import logging
import re

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_SCAN_INTERVAL, CONF_URL, DEFAULT_SCAN_INTERVAL_MINUTES, DEFAULT_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)
LEVELS = ("No Data", "None", "Low", "Moderate", "High", "Very High")


@dataclass
class PollenData:
    level: str
    allergens: list[str]
    forecast: dict[str, str]
    source_updated: str | None
    source_url: str


def _plain_text(page: str) -> str:
    page = re.sub(r"<script[^>]*>.*?</script>", " ", page, flags=re.I | re.S)
    page = re.sub(r"<style[^>]*>.*?</style>", " ", page, flags=re.I | re.S)
    page = re.sub(r"<[^>]+>", " ", page)
    return re.sub(r"\s+", " ", unescape(page)).strip()


def _first_level(text: str) -> str | None:
    for level in sorted(LEVELS, key=len, reverse=True):
        if re.search(rf"\b{re.escape(level)}\b", text, re.I):
            return level
    return None


def parse_pollen_page(page: str, source_url: str) -> PollenData:
    text = _plain_text(page)
    if "Pollen" not in text:
        raise ValueError("The response did not contain pollen content")

    updated_match = re.search(r"Updated on\s+(.+?)(?=\s+Today\b)", text, re.I)
    source_updated = updated_match.group(1).strip() if updated_match else None

    forecast: dict[str, str] = {}
    day_match = re.search(
        r"\bToday\b\s+(.*?)\s+\bTomorrow\b\s+(.*?)\s+\b(?:Saturday|Sunday|Monday|Tuesday|Wednesday|Thursday|Friday)\b\s+(.*?)(?=\s+Top Allergens\b)",
        text,
        re.I,
    )
    if day_match:
        labels = ("today", "tomorrow", "day_3")
        for label, segment in zip(labels, day_match.groups(), strict=True):
            level = _first_level(segment)
            if level:
                forecast[label] = level

    outlook = re.search(r"Pollen Outlook.*?\bToday\b(.*?)(?=\bTop Allergens\b)", text, re.I)
    level = forecast.get("today") or (_first_level(outlook.group(1)) if outlook else None)
    if not level:
        raise ValueError("Unable to locate the current pollen level; the source layout may have changed")

    allergens: list[str] = []
    allergen_match = re.search(r"Top Allergens\s+(.*?)(?=\s+3 Day Pollen Forecast\b)", text, re.I)
    if allergen_match:
        raw = allergen_match.group(1).strip()
        raw = re.sub(r"\bData provided by.*$", "", raw, flags=re.I)
        known = [
            "Ragweed", "True Grasses", "Grass", "Mould", "Mold", "Elm", "Maple",
            "Oak", "Birch", "Ash", "Cedar", "Pine", "Poplar", "Willow", "Alder"
        ]
        allergens = [item for item in known if re.search(rf"\b{re.escape(item)}\b", raw, re.I)]
        allergens = list(dict.fromkeys(allergens))

    return PollenData(level, allergens, forecast, source_updated, source_url)


class LondonPollenCoordinator(DataUpdateCoordinator[PollenData]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        minutes = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=minutes),
            always_update=True,
        )

    async def _async_update_data(self) -> PollenData:
        url = self.entry.data.get(CONF_URL, DEFAULT_URL)
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(
                url,
                headers={"User-Agent": "HomeAssistant LondonPollen/1.0"},
                timeout=30,
            ) as response:
                response.raise_for_status()
                page = await response.text()
            return parse_pollen_page(page, url)
        except Exception as err:
            raise UpdateFailed(f"Unable to update London pollen forecast: {err}") from err
