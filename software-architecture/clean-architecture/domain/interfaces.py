# DOMAIN LAYER - Interfaces (Contracts)
# Business layer defines WHAT it needs, not HOW

from abc import ABC, abstractmethod

## "Repository" = a storage abstraction that hides how/where data is actually stored.
class UserRepository(ABC):
    """Interface - Business layer depends on this, not concrete DB."""

    @abstractmethod
    def get_all(self) -> list:
        pass

    @abstractmethod
    def get_by_id(self, user_id: int):
        pass

    @abstractmethod
    def create(self, name: str, email: str) -> dict:
        pass

    @abstractmethod
    def delete(self, user_id: int) -> bool:
        pass
