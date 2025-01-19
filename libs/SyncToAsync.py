from functools import wraps, partial
import asyncio
from concurrent.futures import ThreadPoolExecutor


class ToAsync:
    def __init__(self, *, executor: ThreadPoolExecutor = None):
        self.executor = executor

    def __call__(self, blocking):
        @wraps(blocking)
        async def wrapper(*args, **kwargs):
            return await asyncio.to_thread(blocking, *args, **kwargs)

        return wrapper


# from concurrent.futures import ThreadPoolExecutor
# from functools import wraps, partial
# import asyncio
#
#
# class to_async:
#     def __init__(self, *, executor: [ThreadPoolExecutor] = None):
#         self.executor = executor
#
#     def __call__(self, blocking):
#         @wraps(blocking)
#         async def wrapper(*args, **kwargs):
#             loop = asyncio.get_event_loop()
#             if not self.executor:
#                 self.executor = ThreadPoolExecutor()
#             func = partial(blocking, *args, **kwargs)
#             return await loop.run_in_executor(self.executor, func)
#
#         return wrapper
