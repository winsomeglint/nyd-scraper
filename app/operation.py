import inspect
import functools

def operation(func):
    @functools.wraps(func)
    def ret_fn(self, *args, **kwargs):
        if self is None or not hasattr(self, 'terminate'):
            return
        err = None
        operation = inspect.stack()[1][3]
        try:
            func(self, *args, **kwargs)
        except Exception as e:
            err = e
        self.terminate(operation=operation, err=err)
    return ret_fn
