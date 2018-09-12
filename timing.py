import time
import threading


class Timer:
    __duration = 60
    __startTime = 0

    def __init__(self, name='timer'):
        self.name = name
        self.__delta = 0
        self.__function = None
        self.__timer = None

    def set_duration(self, sec):
        self.__duration = sec

    def get_duration(self):
        return self.__duration

    def start(self, func):
        self.__startTime = time.time()
        self.__delta = 0
        self.__function = func
        self.__timer = threading.Timer(self.__duration, func)
        self.__timer.start()

    def pause(self):
        self.__delta = self.get_time()
        if self.__delta < self.__duration:
            self.__timer.cancel()

    def resume(self):
        self.__startTime = time.time()
        if self.__delta < self.__duration:
            self.__timer = threading.Timer(self.__duration - self.__delta, self.__function)
            self.__timer.start()

    def get_time(self):
        # TODO: Handle ending of the timer
        return time.time() - self.__startTime + self.__delta









