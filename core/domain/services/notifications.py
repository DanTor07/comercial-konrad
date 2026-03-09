from abc import ABC, abstractmethod

class Observer(ABC):
    @abstractmethod
    def update(self, event_type: str, data: dict):
        pass

class Subject:
    def __init__(self):
        self._observers = []

    def attach(self, observer: Observer):
        self._observers.append(observer)

    def notify(self, event_type: str, data: dict):
        for observer in self._observers:
            observer.update(event_type, data)

class EmailNotificationObserver(Observer):
    def update(self, event_type: str, data: dict):
        # In a real app, use Django's send_mail here
        print(f"Email enviado para evento {event_type}: {data.get('message')}")

class DashboardUpdateObserver(Observer):
    def update(self, event_type: str, data: dict):
        print(f"KPI actualizado en BAM para evento {event_type}")
