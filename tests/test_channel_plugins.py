from dataclasses import dataclass

from typer.testing import CliRunner

from nanobot.bus.queue import MessageBus
from nanobot.channels.base import BaseChannel
from nanobot.channels.manager import ChannelManager
from nanobot.cli.commands import app
from nanobot.config.schema import ChannelPluginConfig, Config

runner = CliRunner()


@dataclass
class _FakeEntryPoint:
    name: str
    value: object

    def load(self):
        return self.value


class _FakeEntryPoints(list):
    def select(self, *, group: str):
        if group == "nanobot.channel_factories":
            return self
        return []


class _PluginChannel(BaseChannel):
    name = "plugin_demo"
    display_name = "Plugin Demo"

    async def start(self) -> None:
        self._running = True

    async def stop(self) -> None:
        self._running = False

    async def send(self, msg) -> None:
        return None


def test_load_channel_factories_from_entry_points(monkeypatch):
    import nanobot.channels.channel_plugins as channel_plugins

    def _factory(**_kwargs):
        return object()

    monkeypatch.setattr(
        channel_plugins.importlib_metadata,
        "entry_points",
        lambda: _FakeEntryPoints([_FakeEntryPoint("plugin-demo", _factory)]),
    )

    factories = channel_plugins.load_channel_factories()

    assert "plugin_demo" in factories
    assert callable(factories["plugin_demo"])


def test_channel_manager_loads_plugin_channel(monkeypatch):
    config = Config()
    config.channels.plugins["plugin-demo"] = ChannelPluginConfig.model_validate(
        {
            "enabled": True,
            "allowFrom": ["*"],
        }
    )

    monkeypatch.setattr("nanobot.channels.registry.discover_channel_names", lambda: [])

    def _factory(*, config, bus, channel_name, app_config):
        assert channel_name == "plugin_demo"
        return _PluginChannel(app_config, bus)

    monkeypatch.setattr("nanobot.channels.manager.get_channel_factory", lambda name: _factory)

    manager = ChannelManager(config, MessageBus())

    assert "plugin_demo" in manager.channels
    assert manager.channels["plugin_demo"].display_name == "Plugin Demo"


def test_channels_status_lists_plugin_channel(monkeypatch):
    config = Config()
    config.channels.plugins["plugin-demo"] = ChannelPluginConfig.model_validate(
        {
            "enabled": True,
        }
    )

    monkeypatch.setattr("nanobot.config.loader.load_config", lambda: config)
    monkeypatch.setattr("nanobot.channels.registry.discover_channel_names", lambda: [])
    monkeypatch.setattr("nanobot.channels.channel_plugins.get_channel_factory", lambda _name: None)

    result = runner.invoke(app, ["channels", "status"])

    assert result.exit_code == 0
    assert "plugin-demo (plugin)" in result.stdout
