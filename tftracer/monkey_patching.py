#! /usr/bin/env python -u
# coding=utf-8

__author__ = 'Sayed Hadi Hashemi'


def __add_tracing_server_hook(hooks):
    if hooks is None:
        return [hook_inject.__tracing_server.hook]
    else:
        hooks = list(hooks)
        hooks.append(hook_inject.__tracing_server.hook)
        return hooks


def __new_init(*args, **kwargs):
    if hook_inject.__original_init is None:
        return

    if "hooks" in hook_inject.__original_init.__code__.co_varnames:
        hooks_index = hook_inject.__original_init.__code__.co_varnames.index("hooks")
        if len(args) > hooks_index:
            args = list(args)
            args[hooks_index] = __add_tracing_server_hook(args[hooks_index])
        else:
            kwargs["hooks"] = __add_tracing_server_hook(kwargs.get("hooks", None))
    else:
        print("'hooks' not in '_MonitoredSession'")

    hook_inject.__original_init(*args, **kwargs)


def hook_inject(*args, **kwargs):
    """
    (Experimental) Injects a tracing server hook to all instances of ``MonitoredSession`` by by monkey patching
    the initializer. This function is an alternative to adding `hooks` to estimator or sessions.
    Be aware, monkey patching could cause unexpected errors and is not recommended.

    This function should be called once in the main script preferably before importing anything else.

    Example:

    .. code-block:: python

        import tftracer
        tftracer.hook_inject()
        ...

        estimator.train(input_fn)


    Args:
        **kwargs: same as :class:`tftracer.TracingServer`.

    Note:
        Monkey Patching (as :class:`tftracer.TracingServer`) works only with subclasses of ``MonitoredSession``.
        For other ``Session`` types, use :class:`tftracer.Timeline`.



    """
    from . import TracingServer
    from tensorflow.python.training.monitored_session import _MonitoredSession

    if hook_inject.__original_init is None:
        hook_inject.__original_init = _MonitoredSession.__init__
        hook_inject.__tracing_server = TracingServer(*args, **kwargs)
        _MonitoredSession.__init__ = __new_init


hook_inject.__tracing_server = None
hook_inject.__original_init = None
