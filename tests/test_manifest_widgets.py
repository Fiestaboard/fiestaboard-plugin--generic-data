"""The settings widgets this manifest asks core to render.

``mappings`` uses core's generic JSON path mapper. The widget knows the shape
of the job — probe a URL, browse the response, map paths onto variables — and
this manifest tells it which of *this* plugin's properties hold each part, so
core carries no knowledge of generic_data.
"""

import json
from pathlib import Path

_MANIFEST = json.loads((Path(__file__).resolve().parent.parent / "manifest.json").read_text())
_PROPERTIES = _MANIFEST["settings_schema"]["properties"]
_MAPPINGS = _PROPERTIES["mappings"]

# The core release that named the widget for its capability and taught it to
# read `probe`/`keys`. Below this, the field degrades to a plain array of
# objects, so the floor holds the plugin update back rather than shipping a
# worse editor.
MIN_CORE_VERSION = (8, 25, 5)


def test_mappings_uses_the_capability_named_widget():
    """Not ``generic-data-mapping-helper``: nothing about the widget is ours."""
    assert _MAPPINGS["ui:widget"] == "json-path-mapper"


def test_probe_names_this_plugins_own_request_properties():
    """Every part of the probe request maps to a property we actually declare."""
    probe = _MAPPINGS["ui:options"]["probe"]

    assert probe == {
        "url": "url",
        "format": "format",
        "method": "method",
        "headers": "headers",
        "body": "body",
    }
    for part, prop in probe.items():
        assert prop in _PROPERTIES, f"probe.{part} names undeclared property {prop!r}"


def test_keys_names_the_properties_a_mapping_row_actually_has():
    """A row the widget writes must be a row this plugin can read back."""
    keys = _MAPPINGS["ui:options"]["keys"]
    row_properties = _MAPPINGS["items"]["properties"]

    assert keys == {"variable": "variable", "path": "path", "default": "default"}
    for part, prop in keys.items():
        assert prop in row_properties, f"keys.{part} names undeclared row key {prop!r}"


def test_the_core_floor_covers_the_widget_this_manifest_asks_for():
    """A core below the floor renders a plain array field instead of the mapper.

    The floor is what holds the hourly plugin auto-update back on those cores,
    so they keep the version of this manifest they can render properly.
    """
    constraint = _MANIFEST["fiestaboard_version"]

    assert constraint.startswith(">="), constraint
    floor = tuple(int(part) for part in constraint[2:].split("."))
    assert floor >= MIN_CORE_VERSION, f"{constraint} predates json-path-mapper"
