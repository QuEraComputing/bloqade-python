from abc import ABC, abstractmethod

class Ansatz(ABC):
    @abstractmethod
    def ansatz(self):
        pass