"""Unit test for tracer.remove_hook"""

from tracer.tracer import clear_hooks, null_trace_hook, remove_hook


def test_remove():
    """
    Test class for test for tracer.remove_hook
    """
    assert remove_hook(null_trace_hook) is None
    clear_hooks()
    assert remove_hook(null_trace_hook) is None
