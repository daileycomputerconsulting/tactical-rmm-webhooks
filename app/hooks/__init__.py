#
import sys
import importlib

__all__ = ["ping", "push"]
# CHECKME: import hooks here
# from . import ping
importlib.import_module("hooks.tactical_rmm", "tactical_api")
for hook in __all__:
    importlib.import_module(".%s" % hook, "hooks")


def get_hooks():
    return [
        k.replace("hooks.", "")
        for k in list(sys.modules.keys())
        if k.startswith("hooks.") and not k.startswith('hooks.tactical_rmm.')
    ]


def has_hook(hook):
    return hook in get_hooks()


def run_hook(hook, payload=None):
    if getattr(sys.modules["hooks.%s" % hook], "run", None) is None:
        mod_name = "hooks.tactical_rmm"
    mod_name = "hooks.%s" % hook
    try:
        return getattr(sys.modules[mod_name], "run")(payload)
    except Exception as e:
        return {"exception": e}
