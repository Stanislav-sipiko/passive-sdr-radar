def timer(func):
    import time
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"[utils] {func.__name__} took {time.time()-start:.2f}s")
        return result
    return wrapper

def calibrate_tools():
    print("[utils] Calibration tool (stub)")
