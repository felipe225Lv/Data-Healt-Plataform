"""Autenticación de usuarios (RF-01)."""

from datetime import timedelta

from app.core import clock
from app.core.exceptions import AccountLockedError, InvalidCredentialsError
from app.domain.models import TokenResponse


class AuthService:
    def __init__(self, user_repository, password_hasher, token_provider,
                 max_attempts: int = 5, lock_minutes: int = 15):
        self.users = user_repository
        self.hasher = password_hasher
        self.tokens = token_provider
        self.max_attempts = max_attempts
        self.lock_minutes = lock_minutes

    def authenticate(self, email: str, password: str) -> TokenResponse:
        user = self.users.get_by_email(email)
        if user is None or not user.is_active:
            raise InvalidCredentialsError()

        now = clock.now()
        if user.locked_until is not None and now < user.locked_until:
            raise AccountLockedError()

        if not self.hasher.verify(password, user.password_hash):
            user.failed_attempts += 1
            if user.failed_attempts >= self.max_attempts:
                user.locked_until = now + timedelta(minutes=self.lock_minutes)
                self.users.update(user)
                raise AccountLockedError()
            self.users.update(user)
            raise InvalidCredentialsError()

        user.failed_attempts = 0
        user.locked_until = None
        self.users.update(user)
        token = self.tokens.create_access_token(subject=user.id, role=user.role)
        return TokenResponse(access_token=token, token_type="bearer")
