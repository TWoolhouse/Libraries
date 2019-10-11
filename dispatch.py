import threading
import queue

class Dispatcher:
    """Dispatcher to distribute tasks over 'num' number of threads."""
    def __init__(self, num=1):
        self.workers = {threading.Thread(target=self._dispatch) for i in range(num)}
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
        """Append Queue 'key' to Queue of data to be processed."""
        self.queue.put(key)
        if not self.event.is_set():
            self.next()

    def __getitem__(self, key):
        """Return iterable of output from 'key'."""
        queue = self.output[key]
        try:
            for i in range(queue.qsize()):
                r = queue.get()
                queue.task_done()
                yield r
        except queue.Empty: return

    def __setitem__(self, key, data):
        """Append 'data' to Queue 'key'."""
        self.data[key][0].put(data)

    def new(self, key: str, func: callable=None, value: object=None, output: bool=False):
        """Create new Queue 'key'

        If 'func' is present, for every 'item' in Queue, 'func' will be called with the 'item' as it's first argument.
        If 'value' if present, it will be passed as an argument to every 'item' in Queue.
        If both are present, 'func' will be called with 'value' as it's first parameter and 'item' as it's second.

        Args:
            key (str): Name of Queue.
            func (callable): Function to called per data in Queue.
            value (obj): Value to passed to callable data from Queue.
            output (bool): Whether to store an output in a seperate Queue.

        """
        self.data[key] = (queue.Queue(), func, value, output)
        if output:
            self.output[key] = queue.Queue()

    def next(self):
        """
        Start Processing the next Queue
        """
        self.event.clear()
        try:
            key = self.queue.get_nowait()
            self.active = key
            self.queue.task_done()
            self.event.set()
        except queue.Empty: pass

    """
    The nested if/else statements are to improve performance by a small margine
    due to the redundancy to perform the check every element in the queue.
    """

    def _dispatch(self):
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
        """Halt execution untill Queue 'key' has processed all data."""
        self.data[key][0].join()

    def stop(self):
        """Halt all threads."""
        self.running.clear()
        self.event.set()
