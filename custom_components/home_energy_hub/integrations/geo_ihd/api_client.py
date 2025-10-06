"""API client for Geo Home IHD."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import aiohttp

_LOGGER = logging.getLogger(__name__)


class GeoHomeAPIClient:
    """Client for Geo Home API."""

    def __init__(self, username: str, password: str, base_url: str = "https://api.geotogether.com") -> None:
        self.username = username
        self.password = password
        self.base_url = base_url
        self._session: Optional[aiohttp.ClientSession] = None
        self._token: Optional[str] = None
        self._token_expires: Optional[datetime] = None

    async def __aenter__(self):
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._close_session()

    async def _ensure_session(self) -> None:
        """Ensure aiohttp session is created."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()

    async def _close_session(self) -> None:
        """Close aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _make_request(self, url: str, method: str = 'GET', headers: Optional[Dict[str, str]] = None,
                           json_body: Optional[Dict[str, Any]] = None, retries: int = 3) -> Dict[str, Any]:
        """Make HTTP request with retry logic."""
        await self._ensure_session()
        full_url = self.base_url + url
        request_headers = headers or {}

        for attempt in range(retries):
            try:
                async with self._session.request(method, full_url, headers=request_headers, json=json_body) as response:
                    response.raise_for_status()
                    return await response.json()
            except aiohttp.ClientError as err:
                if attempt == retries - 1:
                    raise err
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

    async def authenticate(self) -> str:
        """Authenticate and get access token."""
        if self._token and self._token_expires and datetime.now() < self._token_expires:
            return self._token

        headers = {'Content-Type': 'application/json'}
        body = {'identity': self.username, 'password': self.password}

        try:
            response = await self._make_request('/usersservice/v2/login', 'POST', headers=headers, json_body=body)
            self._token = response['accessToken']
            self._token_expires = datetime.now() + timedelta(hours=1)  # Token typically lasts 1 hour
            return self._token
        except aiohttp.ClientResponseError as err:
            if err.status == 401:
                raise ValueError("Invalid username or password")
            raise ValueError(f"Authentication failed: {err}")

    async def get_device_data(self) -> Dict[str, Any]:
        """Get user device data."""
        token = await self.authenticate()
        headers = {'Authorization': f"Bearer {token}"}
        return await self._make_request('/api/userapi/v2/user/detail-systems?systemDetails=true', 'GET', headers=headers)

    async def get_periodic_meter_data(self, system_id: str) -> Dict[str, Any]:
        """Get periodic meter data."""
        token = await self.authenticate()
        headers = {'Authorization': f"Bearer {token}"}
        return await self._make_request(f"/api/userapi/system/smets2-periodic-data/{system_id}", 'GET', headers=headers)

    async def get_live_meter_data(self, system_id: str) -> Dict[str, Any]:
        """Get live meter data."""
        token = await self.authenticate()
        headers = {'Authorization': f"Bearer {token}"}
        return await self._make_request(f"/api/userapi/system/smets2-live-data/{system_id}", 'GET', headers=headers)