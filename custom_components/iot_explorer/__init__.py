from .panel import create_panel

async def async_setup_entry(hass, entry):
    # ... existing setup logic ...

    # Start the panel
    panel_app = create_panel(hass, DOMAIN)
    hass.http.register_view(panel_app)