from functools import wraps

from globals import GlobalState
from utils import update_table, update_status


def save_state(func):
    """
    Decorator to dump the state to disk after function is run
    """
    @wraps(func)
    async def decorated(*args, **kwargs):
        await func(*args, **kwargs)
        state = GlobalState()
        state.save_current_state()
        await update_status()
        await update_table()
    return decorated
