import time

def constrain(n, start1, stop1, start2, stop2):
  return ((n - start1) / (stop1 - start1)) * (stop2 - start2) + start2

def clamp(n, start, stop):
    if n < start:
        return start
    if n > stop:
        return stop

def record_time(output=None):
    def record_time(func):
        if output == None:
            def record_time(*args, **kwargs):
                start = time.time()
                res = func(*args, **kwargs)
                end = time.time()
                print("Time Taken: {:.3f}s".format((end-start)))
                return res
        elif output == True:
            def record_time(*args, **kwargs):
                start = time.time()
                res = func(*args, **kwargs)
                end = time.time()
                print("Time Taken: {:.3f}s".format((end-start)))
                return end-start
        else:
            def record_time(*args, **kwargs):
                return func(*args, **kwargs)
        return record_time
    return record_time
