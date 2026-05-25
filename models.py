from interfaces import Observer

class ActivitySubject:
    def __init__(self, name: str):
        self.name = name
        self._observers = []

    def attach(self, observer: Observer):
        if observer not in self._observers:
            self._observers.append(observer)

    def notify(self):
        for obs in self._observers:
            obs.update(self.name)

    def mark_completed(self):
        self.notify()