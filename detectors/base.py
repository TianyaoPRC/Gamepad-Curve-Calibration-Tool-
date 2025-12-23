from abc import ABC, abstractmethod


class AngleDetector(ABC):
    @abstractmethod
    def wait_start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def wait_stop(self) -> None:
        raise NotImplementedError
