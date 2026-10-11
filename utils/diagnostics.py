import time, functools
from contextlib import contextmanager

def timed(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        try:
            return fn(*args, **kwargs)
        finally:
            print(f"{fn.__qualname__}: {(time.perf_counter() - t0) * 1000:.2f} ms")
    return wrapper

@contextmanager
def performance(label, threshold_ms=0.5):
    t0 = time.perf_counter()
    yield
    ms = (time.perf_counter() - t0) * 1000
    if ms > threshold_ms:
        print(f"{label}: {ms:.2f} ms")