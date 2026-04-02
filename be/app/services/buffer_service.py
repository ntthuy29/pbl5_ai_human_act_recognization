from collections import deque

class BufferService:
    def __init__(self, max_size=128):
        self.buffer = deque(maxlen=max_size)
        self.max_size = max_size

    def add_sample(self, sample):
        self.buffer.append(sample)

    def is_ready(self):
        return len(self.buffer) == self.max_size

    def get_window(self):
        if not self.is_ready():
            return None
        return list(self.buffer)

buffer_service = BufferService(max_size=128)