"""Gestión de usuarios (RF-08)."""

from app.core.exceptions import BusinessRuleError, DuplicateEmailError, NotFoundError
from app.domain.models import User, UserCreateDTO, UserOut, UserUpdateDTO


class UserService:
    def __init__(self, user_repository, password_hasher):
        self.users = user_repository
        self.hasher = password_hasher

    def create_user(self, dto: UserCreateDTO) -> UserOut:
        if self.users.get_by_email(dto.email) is not None:
            raise DuplicateEmailError()
        user = User(
            id=None,
            full_name=dto.full_name,
            email=dto.email,
            password_hash=self.hasher.hash(dto.password),
            role=dto.role,
            is_active=True,
        )
        return UserOut.from_entity(self.users.add(user))

    def update_user(self, user_id: int, dto: UserUpdateDTO) -> UserOut:
        user = self._get(user_id)
        if dto.full_name is not None:
            user.full_name = dto.full_name
        if dto.role is not None:
            user.role = dto.role
        return UserOut.from_entity(self.users.update(user))

    def deactivate_user(self, user_id: int, requester_id: int) -> bool:
        user = self._get(user_id)
        if user_id == requester_id:
            raise BusinessRuleError("No puede desactivar su propia cuenta")
        user.is_active = False
        self.users.update(user)
        return True

    def list_users(self, role: str | None = None, only_active: bool = True) -> list[UserOut]:
        users = self.users.list(role=role, is_active=True if only_active else None)
        return [UserOut.from_entity(u) for u in users]

    def _get(self, user_id: int) -> User:
        user = self.users.get_by_id(user_id)
        if user is None:
            raise NotFoundError("Usuario no encontrado")
        return user
