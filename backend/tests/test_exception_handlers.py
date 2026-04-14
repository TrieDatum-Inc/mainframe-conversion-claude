"""
Unit tests for exception handlers and custom error classes.

Covers app.exceptions.errors and app.exceptions.handlers branches
that are not exercised by the auth endpoint tests.
"""

import pytest
from fastapi import HTTPException
from httpx import AsyncClient, ASGITransport

from app.exceptions.errors import (
    AuthenticationError,
    CardDemoException,
    InvalidTokenError,
)


class TestCustomExceptions:
    """Tests for CardDemoException hierarchy."""

    def test_card_demo_exception_attributes(self):
        exc = CardDemoException(message="Something went wrong", error_code="DEMO_ERROR")
        assert exc.message == "Something went wrong"
        assert exc.error_code == "DEMO_ERROR"
        assert str(exc) == "Something went wrong"

    def test_authentication_error_defaults(self):
        exc = AuthenticationError()
        assert exc.error_code == "AUTHENTICATION_ERROR"
        assert "Authentication failed" in exc.message

    def test_authentication_error_custom_message(self):
        exc = AuthenticationError(message="Token expired")
        assert exc.message == "Token expired"
        assert exc.error_code == "AUTHENTICATION_ERROR"

    def test_invalid_token_error_defaults(self):
        exc = InvalidTokenError()
        assert exc.error_code == "INVALID_TOKEN"
        assert "credentials" in exc.message.lower()

    def test_invalid_token_error_custom_message(self):
        exc = InvalidTokenError(message="JWT signature mismatch")
        assert exc.message == "JWT signature mismatch"

    def test_exception_is_instance_of_base(self):
        auth_exc = AuthenticationError()
        assert isinstance(auth_exc, CardDemoException)
        assert isinstance(auth_exc, Exception)


class TestExceptionHandlers:
    """Tests for the global exception handlers registered in main.py."""

    @pytest.fixture
    def app_with_test_routes(self):
        """Create a FastAPI app with routes that trigger various exception types."""
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        from app.exceptions.handlers import register_exception_handlers

        app = FastAPI()
        register_exception_handlers(app)

        @app.get("/http-error")
        async def raise_http_error():
            raise HTTPException(status_code=404, detail="Not found")

        @app.get("/http-error-dict")
        async def raise_http_error_dict():
            raise HTTPException(
                status_code=401,
                detail={"error_code": "UNAUTHORIZED", "message": "Not allowed"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        @app.get("/server-error")
        async def raise_server_error():
            raise HTTPException(status_code=500, detail="Internal server error")

        @app.get("/unhandled-error")
        async def raise_unhandled():
            raise RuntimeError("Something unexpected happened")

        @app.post("/validation-error")
        async def validation_endpoint(body: dict):
            return body

        return app

    @pytest.mark.asyncio
    async def test_http_exception_plain_string_detail(self, app_with_test_routes):
        async with AsyncClient(
            transport=ASGITransport(app=app_with_test_routes),
            base_url="http://testserver",
        ) as client:
            response = await client.get("/http-error")
        assert response.status_code == 404
        data = response.json()
        assert data["error_code"] == "HTTP_ERROR"
        assert "Not found" in data["message"]

    @pytest.mark.asyncio
    async def test_http_exception_dict_detail(self, app_with_test_routes):
        async with AsyncClient(
            transport=ASGITransport(app=app_with_test_routes),
            base_url="http://testserver",
        ) as client:
            response = await client.get("/http-error-dict")
        assert response.status_code == 401
        data = response.json()
        assert data["error_code"] == "UNAUTHORIZED"
        assert data["message"] == "Not allowed"

    @pytest.mark.asyncio
    async def test_server_error_500_logged(self, app_with_test_routes):
        async with AsyncClient(
            transport=ASGITransport(app=app_with_test_routes),
            base_url="http://testserver",
        ) as client:
            response = await client.get("/server-error")
        assert response.status_code == 500
        data = response.json()
        assert data["error_code"] == "HTTP_ERROR"

    @pytest.mark.asyncio
    async def test_unhandled_exception_handler_directly(self):
        """
        Call the unhandled_exception_handler function directly to verify
        it returns the correct 500 response without routing through ASGI middleware.
        """
        from unittest.mock import AsyncMock, MagicMock
        from fastapi import FastAPI, Request
        from app.exceptions.handlers import register_exception_handlers

        app = FastAPI()
        register_exception_handlers(app)

        # Call the handler directly via the registered exception handlers
        # The catch-all handler is at index for 'Exception' in app.exception_handlers
        handler = app.exception_handlers.get(Exception)
        assert handler is not None, "Exception handler not registered"

        mock_request = MagicMock(spec=Request)
        mock_request.url = MagicMock()
        mock_request.url.__str__ = lambda self: "http://testserver/unhandled-error"

        exc = RuntimeError("Something unexpected happened")
        response = await handler(mock_request, exc)

        assert response.status_code == 500
        import json
        data = json.loads(response.body)
        assert data["error_code"] == "INTERNAL_SERVER_ERROR"
        assert "unexpected" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_validation_error_returns_422(self, app_with_test_routes):
        """Sending wrong content type triggers RequestValidationError."""
        from pydantic import BaseModel
        from fastapi import FastAPI
        from app.exceptions.handlers import register_exception_handlers
        from fastapi.responses import JSONResponse

        app = FastAPI()
        register_exception_handlers(app)

        class Item(BaseModel):
            name: str
            count: int

        @app.post("/items")
        async def create_item(item: Item):
            return item

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            response = await client.post(
                "/items",
                json={"name": "test"},  # missing 'count'
            )
        assert response.status_code == 422
        data = response.json()
        assert data["error_code"] == "VALIDATION_ERROR"
        assert "details" in data
