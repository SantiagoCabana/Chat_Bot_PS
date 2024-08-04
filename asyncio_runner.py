import asyncio
import threading

class AsyncioRunner:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.loop.run_forever)
        self.thread.daemon = True

    def start(self):
        self.thread.start()

    def stop(self):
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join()

    def run_task(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self.loop)
