"""
MODULE: Plugin State
DESCRIPTION: Holds global state references for loaded plugins and their configurations.
"""

REGISTRY_PATH = "core/registry.json"

# Stores configuration schemas collected from plugins
_plugin_config_schemas = {}

# Active plugins (Native and Legacy)
_loaded_plugins = {}          # tag -> module (for JSON Calling / old single plugins)
_loaded_legacy_plugins = {}   # tag -> instance of LegacyPlugin class

def get_active_tags():
    """Returns a list of all currently active plugin tags."""
    return list(_loaded_plugins.keys()) + list(_loaded_legacy_plugins.keys())

def get_plugin_module(tag, legacy=False):
    """Returns the plugin module if active, otherwise None."""
    if legacy:
        return _loaded_legacy_plugins.get(tag)
    return _loaded_plugins.get(tag)
