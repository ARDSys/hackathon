from abc import ABC, abstractmethod
class Module(ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def forward(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        return self.forward(*args, **kwargs)

