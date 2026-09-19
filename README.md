# London Pollen Forecast for Home Assistant

A HACS-compatible custom integration that creates Home Assistant sensors from The Weather Network's London, Ontario pollen page.

## Entities

- **Level**: current pollen level such as Low, Moderate, High, or Very High
- **Top allergens**: comma-separated allergens reported on the source page
- The Level sensor also exposes `forecast`, `top_allergens`, `source_updated`, `source_url`, and attribution attributes.

## Install through HACS as a custom repository

1. Put this project in a public GitHub repository.
2. Replace `YOUR_GITHUB_USERNAME` in `custom_components/london_pollen/manifest.json`.
3. In HACS, open **Integrations**, select the three-dot menu, then **Custom repositories**.
4. Add the repository URL and choose **Integration**.
5. Install **London Pollen Forecast** and restart Home Assistant.
6. Go to **Settings > Devices & services > Add integration** and search for **London Pollen Forecast**.

## Manual installation

Copy `custom_components/london_pollen` to `/config/custom_components/london_pollen`, restart Home Assistant, and add the integration through **Settings > Devices & services**.

## Update interval

The default is 360 minutes. Change it under the integration's **Configure** button. The allowed range is 60 to 1440 minutes.

## Important limitation

This integration parses a third-party consumer web page. If that page changes its wording or HTML structure, the integration may report an update failure until its parser is updated. A licensed or documented API would be more reliable for production use.

## Example automation

```yaml
alias: London pollen warning
triggers:
  - trigger: state
    entity_id: sensor.london_pollen_level
    to:
      - High
      - Very High
actions:
  - action: notify.notify
    data:
      title: London pollen warning
      message: >-
        Pollen is {{ states('sensor.london_pollen_level') }}.
        Top allergens: {{ state_attr('sensor.london_pollen_level', 'top_allergens') | join(', ') }}
mode: single
```

## Data source and use

The source page is The Weather Network's London pollen outlook. The page credits Aerobiology Research Laboratories for pollen forecast data. Review the source site's terms before redistributing, publishing, or heavily polling its content.
