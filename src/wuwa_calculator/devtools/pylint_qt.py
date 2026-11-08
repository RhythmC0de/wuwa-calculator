"""Teach Astroid about compiled PySide signal descriptors, not all attributes.

PySide exposes inherited signals as anonymous methods. Model their three
signal operations without changing inference for dictionaries or widgets.
See https://github.com/pylint-dev/pylint-qt/issues/1.
"""

from astroid import MANAGER, nodes, parse

_SIGNAL = parse("""
class SignalOperations:
    def connect(self, slot, *args, **kwargs): pass
    def disconnect(self, *args, **kwargs): pass
    def emit(self, *args): pass
""")["SignalOperations"]


def _is_pyside_signal(node: nodes.FunctionDef) -> bool:
    if not node.root().name.startswith("PySide6."):
        return False
    return any(
        isinstance(signal_type, nodes.ClassDef)
        and signal_type.name == "Signal"
        and signal_type.root().name.startswith("PySide6.")
        for signal_type in node.instance_attrs.get("__class__", ())
    )


def _add_signal_operations(node: nodes.FunctionDef) -> None:
    for operation in ("connect", "disconnect", "emit"):
        node.instance_attrs[operation] = [_SIGNAL[operation]]


def register(_linter) -> None:
    """Register only the compiled PySide signal descriptor transform."""
    MANAGER.register_transform(
        nodes.FunctionDef, _add_signal_operations, _is_pyside_signal
    )
