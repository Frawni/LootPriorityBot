from functools import wraps

from globals import GlobalState


def save_state(func):
    """
    Decorator to dump the state to disk after function is run
    """
    @wraps(func)
    async def decorated(*args, **kwargs):
        await func(*args, **kwargs)
        state = GlobalState()
        state.save_current_state()
    return decorated
