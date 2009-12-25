Centralized Trace management using sys.settrace.

We allow several trace hooks to get registered and unregistered and
allow tracing to be turned on and off temporarily without losing the
trace hooks. You can also indicate filters on events for which trace
hooks should fire and mark methods that should automatically be
ignored.
