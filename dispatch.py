import threading
import queue

class Dispatcher:
    def __init__(self, num=1):
        self.workers = {threading.Thread(target=self.dispatch) for i in range(num)}
        self.running = threading.Event()
        self.event = threading.Event()
        self.queue = queue.Queue()
        self.active = None
        self.data = {}
        self.output = {}

        self.new(self.active)

        self.running.set()
        for w in self.workers:
            w.start()

    def __call__(self, key):
        self.queue.put(key)
        if not self.event.is_set():
            self.next()

    def __getitem__(self, key):
        queue = self.output[key]
        try:
            for i in range(queue.qsize()):
                r = queue.get()
                queue.task_done()
                yield r
        except queue.Empty: return

    def __setitem__(self, key, data):
        self.data[key][0].put(data)

    def new(self, key, func=None, value=None, output=False):
        self.data[key] = (queue.Queue(), func, value, output)
        if output:
            self.output[key] = queue.Queue()

    def next(self):
        self.event.clear()
        try:
            key = self.queue.get_nowait()
            self.active = key
            self.queue.task_done()
            self.event.set()
        except queue.Empty: pass

    def dispatch(self):
        while self.running.is_set():
            self.event.wait()
            que, func, value, is_output = self.data[self.active]
            try:
                if value:
                    if func:
                        if is_output:
                            output = self.output[self.active]
                            while True:
                                item = que.get_nowait()
                                r = func(value, item)
                                que.task_done()
                                output.put(r)
                        else:
                            while True:
                                item = que.get_nowait()
                                func(value, item)
                                que.task_done()
                    else:
                        if is_output:
                            output = self.output[self.active]
                            while True:
                                item = que.get_nowait()
                                r = item(value)
                                que.task_done()
                                output.put(r)
                        else:
                            while True:
                                item = que.get_nowait()
                                item(value)
                                que.task_done()
                else:
                    if func:
                        if is_output:
                            output = self.output[self.active]
                            while True:
                                item = que.get_nowait()
                                r = func(item)
                                que.task_done()
                                output.put(r)
                        else:
                            while True:
                                item = que.get_nowait()
                                func(item)
                                que.task_done()
                    else:
                        if is_output:
                            output = self.output[self.active]
                            while True:
                                item = que.get_nowait()
                                r = item()
                                que.task_done()
                                output.put(r)
                        else:
                            while True:
                                item = que.get_nowait()
                                item()
                                que.task_done()
            except queue.Empty:
                if not self.event.is_set():
                    continue
                self.next()

    def wait(self, key):
        self.data[key][0].join()

    def stop(self):
        self.running.clear()
        self.event.set()
