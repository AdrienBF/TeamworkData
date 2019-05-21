from abc import ABC, abstractmethod


class BaseDownload(ABC):
    @abstractmethod
    def run(self, input_data):
        pass
