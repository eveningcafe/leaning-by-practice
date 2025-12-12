# BUSINESS LAYER - Business Logic
# NOTE: Directly depends on Data Layer (tight coupling)

from data import user_repository


def register(name: str, email: str) -> dict:
    """Business Rule: Validate before creating."""
    if not name or not email:
        raise ValueError("Name and email required")
    return user_repository.create(name, email)


def get_user(user_id: int) -> dict:
    user = user_repository.get_by_id(user_id)
    if not user:
        raise ValueError("User not found")
    return user


def list_users() -> list:
    return user_repository.get_all()


def remove_user(user_id: int) -> bool:
    if not user_repository.get_by_id(user_id):
        raise ValueError("User not found")
    return user_repository.delete(user_id)
