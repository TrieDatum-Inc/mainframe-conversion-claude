"""
Shared rate limiter instance.

Using a single module-level Limiter ensures the same instance is registered
on app.state in main.py AND referenced by endpoint decorators. Two separate
Limiter instances would not share state, silently defeating rate limiting.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
