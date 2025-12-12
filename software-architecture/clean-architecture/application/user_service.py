# APPLICATION LAYER - Use Cases
# Depends on interface, NOT concrete implementation

from domain.interfaces import UserRepository


class UserService:
    def __init__(self, repo: UserRepository):
        # Dependency Injection - receives interface, not concrete class
        self.repo = repo

    def register(self, name: str, email: str) -> dict:
        if not name or not email:
            raise ValueError("Name and email required")
        return self.repo.create(name, email)

    def get_user(self, user_id: int) -> dict:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        return user

    def list_users(self) -> list:
        return self.repo.get_all()

    def remove_user(self, user_id: int) -> bool:
        if not self.repo.get_by_id(user_id):
            raise ValueError("User not found")
        return self.repo.delete(user_id)
