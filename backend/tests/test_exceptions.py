"""
Unit tests for exceptions/errors.py and exceptions/handlers.py.

Verifies that all CardDemoException subclasses carry correct error codes,
and that the registered HTTP handlers map to the right status codes.
"""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.exceptions.errors import (
    CardDemoException,
    DuplicateResourceError,
    InvalidCredentialsError,
    NoChangesDetectedError,
    NotFoundError,
    OptimisticLockError,
    PermissionDeniedError,
    ValidationError,
)
from app.exceptions.handlers import register_exception_handlers


# =============================================================================
# Error class unit tests
# =============================================================================

class TestNotFoundError:
    def test_error_code_includes_resource(self):
        err = NotFoundError("Account", "12345")
        assert err.error_code == "ACCOUNT_NOT_FOUND"

    def test_message_contains_identifier(self):
        err = NotFoundError("Account", "12345")
        assert "12345" in err.message

    def test_is_carddemo_exception(self):
        err = NotFoundError("User", "U001")
        assert isinstance(err, CardDemoException)


class TestDuplicateResourceError:
    def test_error_code_includes_resource(self):
        err = DuplicateResourceError("User", "U001")
        assert err.error_code == "USER_ALREADY_EXISTS"

    def test_message_contains_identifier(self):
        err = DuplicateResourceError("User", "U001")
        assert "U001" in err.message


class TestInvalidCredentialsError:
    def test_error_code(self):
        err = InvalidCredentialsError()
        assert err.error_code == "INVALID_CREDENTIALS"

    def test_message_is_generic(self):
        """Message must not reveal whether user_id or password was wrong."""
        err = InvalidCredentialsError()
        assert "Invalid User ID or Password" == err.message


class TestPermissionDeniedError:
    def test_error_code(self):
        err = PermissionDeniedError()
        assert err.error_code == "ADMIN_REQUIRED"

    def test_message_mentions_admin(self):
        err = PermissionDeniedError()
        assert "administrator" in err.message.lower()


class TestValidationError:
    def test_custom_error_code(self):
        err = ValidationError("INVALID_FICO", "FICO out of range")
        assert err.error_code == "INVALID_FICO"

    def test_message_passed_through(self):
        err = ValidationError("X", "Custom message")
        assert err.message == "Custom message"


class TestOptimisticLockError:
    def test_error_code(self):
        err = OptimisticLockError("Account")
        assert err.error_code == "OPTIMISTIC_LOCK_ERROR"

    def test_message_contains_resource(self):
        err = OptimisticLockError("CreditCard")
        assert "CreditCard" in err.message

    def test_message_advises_reload(self):
        err = OptimisticLockError("Account")
        assert "reload" in err.message.lower() or "modified" in err.message.lower()


class TestNoChangesDetectedError:
    def test_error_code(self):
        err = NoChangesDetectedError("account")
        assert err.error_code == "NO_CHANGES_DETECTED"

    def test_message_contains_resource(self):
        err = NoChangesDetectedError("account")
        assert "account" in err.message


# =============================================================================
# Exception handler integration tests
# =============================================================================
# Build a minimal FastAPI app with a route for each exception type, then
# verify the handler maps it to the correct HTTP status code.

def _make_test_app() -> FastAPI:
    from sqlalchemy.exc import IntegrityError

    test_app = FastAPI()
    register_exception_handlers(test_app)

    @test_app.get("/not-found")
    async def _not_found():
        raise NotFoundError("Item", "X")

    @test_app.get("/duplicate")
    async def _duplicate():
        raise DuplicateResourceError("Item", "X")

    @test_app.get("/invalid-creds")
    async def _invalid_creds():
        raise InvalidCredentialsError()

    @test_app.get("/permission")
    async def _permission():
        raise PermissionDeniedError()

    @test_app.get("/validation")
    async def _validation():
        raise ValidationError("ERR_CODE", "bad data")

    @test_app.get("/optimistic-lock")
    async def _optimistic_lock():
        raise OptimisticLockError("Account")

    @test_app.get("/no-changes")
    async def _no_changes():
        raise NoChangesDetectedError("account")

    @test_app.get("/integrity")
    async def _integrity():
        raise IntegrityError("", {}, RuntimeError("dup"))

    @test_app.get("/base-exception")
    async def _base():
        raise CardDemoException("SOME_ERR", "Some message")

    return test_app


@pytest.fixture
async def handler_client():
    app = _make_test_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="https://testserver") as ac:
        yield ac


class TestExceptionHandlers:
    @pytest.mark.asyncio
    async def test_not_found_returns_404(self, handler_client: AsyncClient):
        resp = await handler_client.get("/not-found")
        assert resp.status_code == 404
        assert resp.json()["detail"]["error_code"] == "ITEM_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_duplicate_returns_409(self, handler_client: AsyncClient):
        resp = await handler_client.get("/duplicate")
        assert resp.status_code == 409
        assert resp.json()["detail"]["error_code"] == "ITEM_ALREADY_EXISTS"

    @pytest.mark.asyncio
    async def test_invalid_credentials_returns_401(self, handler_client: AsyncClient):
        resp = await handler_client.get("/invalid-creds")
        assert resp.status_code == 401
        assert resp.json()["detail"]["error_code"] == "INVALID_CREDENTIALS"

    @pytest.mark.asyncio
    async def test_permission_denied_returns_403(self, handler_client: AsyncClient):
        resp = await handler_client.get("/permission")
        assert resp.status_code == 403
        assert resp.json()["detail"]["error_code"] == "ADMIN_REQUIRED"

    @pytest.mark.asyncio
    async def test_validation_error_returns_422(self, handler_client: AsyncClient):
        resp = await handler_client.get("/validation")
        assert resp.status_code == 422
        assert resp.json()["detail"]["error_code"] == "ERR_CODE"

    @pytest.mark.asyncio
    async def test_optimistic_lock_returns_409(self, handler_client: AsyncClient):
        resp = await handler_client.get("/optimistic-lock")
        assert resp.status_code == 409
        assert resp.json()["detail"]["error_code"] == "OPTIMISTIC_LOCK_ERROR"

    @pytest.mark.asyncio
    async def test_no_changes_returns_422(self, handler_client: AsyncClient):
        resp = await handler_client.get("/no-changes")
        assert resp.status_code == 422
        assert resp.json()["detail"]["error_code"] == "NO_CHANGES_DETECTED"

    @pytest.mark.asyncio
    async def test_integrity_error_returns_409(self, handler_client: AsyncClient):
        resp = await handler_client.get("/integrity")
        assert resp.status_code == 409
        assert resp.json()["detail"]["error_code"] == "DATABASE_INTEGRITY_ERROR"

    @pytest.mark.asyncio
    async def test_base_exception_returns_400(self, handler_client: AsyncClient):
        resp = await handler_client.get("/base-exception")
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_error_response_has_details_list(self, handler_client: AsyncClient):
        resp = await handler_client.get("/not-found")
        body = resp.json()
        assert "details" in body["detail"]
        assert isinstance(body["detail"]["details"], list)
