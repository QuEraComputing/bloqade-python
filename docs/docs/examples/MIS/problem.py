from abc import ABC, abstractmethod

class Problem(ABC):
    @abstractmethod
    def cost_function(self, ansatz, x):
        pass
