import time
import threading


class Timer:
    __duration = 60
    __startTime = 0

    def __init__(self, name='timer'):
        self.name = name

    def set_duration(self, sec):
        self.__duration = sec

    def start(self, func):
        self.__startTime = time.time()
        t = threading.Timer(self.__duration, func)
        t.start()

    def get_time(self):
        # TODO: Handle ending of the timer
        return time.time() - self.__startTime
