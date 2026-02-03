"""Unit tests for Tracer.trace"""

import sys

import pytest

import tracer
from tracer.sys_monitoring import (
    MAX_TOOL_IDS,
    TOOL_ID_RANGE,
    PytraceException,
    check_tool_id,
    find_hook_by_id,
    find_hook_by_name,
    free_tool_id,
    register_tool_by_name,
)

# FIXME: remove globalness requirement of tests.
# One implication is that we can't run tests in parallel.

def setup_function():
    for tool_id in TOOL_ID_RANGE:
        if tracer.msize() == 0:
            break
        free_tool_id(tool_id)
    assert tracer.msize() == 0
    return


def test_event2short_sanity():
    t = sorted(tracer.EVENT2SHORT.keys())
    assert tracer.ALL_EVENT_NAMES == tuple(
        t
    ), "EVENT2SHORT.keys() should match ALL_EVENT_NAMES"
    return


def test_check_tool_id():
    """Test size, free_tool_id, Basic sanity and status testing."""
    for tool_id in (-1, MAX_TOOL_IDS):
        with pytest.raises(PytraceException):
            check_tool_id(tool_id)


def test_find_hook_fns_size():
    tool_id1 = register_tool_by_name("test_find_hook_fns1")
    tool_id2 = register_tool_by_name("test_find_hook_fns2")
    assert find_hook_by_id(tool_id1) == "test_find_hook_fns1"
    assert find_hook_by_id(tool_id2) == "test_find_hook_fns2"
    assert find_hook_by_name("test_find_hook_fns2") == tool_id2


def test_register_tool_by_name_and_msize():
    for tool_id in TOOL_ID_RANGE:
        tool_name = f"pytest_register_too_by_name_{tool_id}"
        register_tool_by_name(tool_name, can_change_tool_id=False)
        assert (
            tracer.msize() == tool_id + 1
        ), f"msize() should note {tool_id + 1} tool(s) registered"

    # We now have a full list of HOOKS.

    # See that we get an error when trying to add a new one.
    with pytest.raises(PytraceException):
        register_tool_by_name("Should not be able to add", can_change_tool_id=True)

    # Reregistering with the same name id with the same id.
    register_tool_by_name(tool_name, can_change_tool_id=False)
    register_tool_by_name(tool_name, can_change_tool_id=True)

    # Registering a previously_used name under a different id, but
    # not allowing a tool_id change.
    tool_name = "pytest_register_tool_by_name_0"
    with pytest.raises(PytraceException):
        register_tool_by_name(tool_name, tool_id=3, can_change_tool_id=False)

    # Registering a previously_used name, allowing a tool_id change.
    tool_name = "pytest_register_tool_by_name_0"
    with pytest.raises(PytraceException):
        register_tool_by_name(tool_name, tool_id=4, can_change_tool_id=False)

    # We should still have a full list of HOOKS
    assert tracer.msize() == MAX_TOOL_IDS
    return


def test_free_tool_id():
    """Test free_tool_id()"""
    with pytest.raises(PytraceException):
        free_tool_id(20)
    for tool_id in TOOL_ID_RANGE:
        assert tracer.sys_monitoring.TOOL_NAME[tool_id] is None
        assert tracer.sys_monitoring.MONITOR_HOOKS[tool_id] is None
        if (sys.monitoring.get_tool(tool_id)) is not None:
            with pytest.raises(PytraceException):
                free_tool_id(tool_id)
        else:
            tool_name = f"test_free_tool_id_{tool_id}"
            register_tool_by_name(tool_name, tool_id, can_change_tool_id=False)
            free_tool_id(tool_id)
