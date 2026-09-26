"""Board-geometry conformance for the generic_data plugin.

generic_data renders a list of *user-defined* mappings -- the number of
mappings and the length of each mapped value are both unbounded by design
(the whole point of the plugin is "map any field from any API"). That makes
it the textbook case the shared conformance suite exists for: content that
must reflow to whatever board it lands on rather than assuming a Flagship's
22x6.

``strict_growth=True`` because this is exactly the kind of list/feed plugin
the growth check targets -- a taller board must show strictly more mapping
lines when the shorter board was full.
"""

import json
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock

from plugins.generic_data import GenericDataPlugin
from src.plugins.geometry_conformance import assert_board_conformance

MANIFEST = json.loads((Path(__file__).parent.parent / "manifest.json").read_text())

# Comfortably more mappings than the tallest geometry in the suite has rows
# for (max array is 120x24; 22 lines are available for content once the
# header is accounted for), so every rung of the growth ladder still has
# more to show than the last, and the "large number of mappings" case in
# the fix brief is actually exercised rather than trivially satisfied.
_NUM_MAPPINGS = 40

# One deliberately oversized value, to exercise "a very long single value
# degrades sanely at 15x3 and fills usefully at 120x24" -- it must never
# blow out a row's width on any board, narrow or wide.
_LONG_VALUE = "OVERFLOW-" * 40


def _fake_payload() -> Dict[str, Any]:
    payload = {f"field_{i}": f"value-{i}" for i in range(_NUM_MAPPINGS)}
    payload["long_field"] = _LONG_VALUE
    return payload


def _stub_request(payload: Dict[str, Any]):
    """A ``requests.request`` replacement that never touches the network."""

    def _request(method, url, **kwargs):
        response = Mock()
        response.status_code = 200
        response.content = json.dumps(payload).encode()
        response.json.return_value = payload
        response.raise_for_status = Mock()
        return response

    return _request


def _make_plugin_factory(monkeypatch):
    """Build a factory returning a fresh, network-stubbed plugin.

    The suite renders the returned plugin many times and never touches the
    network itself, so the stub is installed once here, up front.
    """
    payload = _fake_payload()
    monkeypatch.setattr("plugins.generic_data.requests.request", _stub_request(payload))

    mappings = [{"variable": f"field_{i}", "path": f"field_{i}"} for i in range(_NUM_MAPPINGS)]
    mappings.append({"variable": "long_value", "path": "long_field"})

    def make_plugin() -> GenericDataPlugin:
        plugin = GenericDataPlugin(MANIFEST)
        plugin.config = {
            "enabled": True,
            "url": "https://example.com/data",
            "format": "json",
            "method": "GET",
            "headers": [],
            "mappings": mappings,
        }
        return plugin

    return make_plugin


def test_renders_on_every_board_shape(monkeypatch):
    make_plugin = _make_plugin_factory(monkeypatch)
    assert_board_conformance(
        make_plugin,
        manifest=MANIFEST,
        strict_growth=True,
        require_note_array_preview=True,
    )
