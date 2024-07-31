import os
import logging

import httpx
from authlib.integrations.httpx_client import AsyncOAuth2Client
from pymemcache import Client, serde

from .cache import InMemoryCache


logging.basicConfig(level=logging.INFO)


class M2MClient(AsyncOAuth2Client):
    """Slightly modified version of the AsyncOAuth2Client from authlib to support caching and loading credentials
    from environment variables. This class is used to make requests to the API with a machine-to-machine token.

    Args:
        service (str): The name of the service to make requests to.
        client_id (str, optional): The client id to use for authentication. Will default to the AUTH0_CLIENT_ID
                                    environment variable.
        client_secret (str, optional): The client secret to use for authentication. Will default to the
                                        AUTH0_CLIENT_SECRET environment variable.
        auth_base_url (str, optional): The base url to use for authentication. Will default to the TOKEN_ENDPOINT
                                        environment variable.
        audience (str, optional): The audience to use for authentication. Will default to the {service}_AUDIENCE
                                    environment variable.
        base_url (str, optional): The base url to use for the API. Will default to the {service}_URL environment
                                    variable.
        cache (Cache, optional): The cache to use for storing tokens. Will default to an InMemoryCache.
        token_cache_buffer (int, optional): The number of seconds to subtract from the token expiry time to ensure the
                                    token is not expired. Will default to 60.
    """

    def __init__(
        self,
        service: str = None,
        client_id: str = None,
        client_secret: str = None,
        auth_base_url: str = None,
        audience: str = None,
        base_url: str = None,
        cache=None,
        token_cache_buffer=60,
    ):
        if service:
            self.service = service.upper()
        elif not all(
            [
                client_id,
                client_secret,
                auth_base_url,
                audience,
                base_url,
            ]
        ):
            raise ValueError(
                "If service is not provided, all of client_id, client_secret, auth_base_url, audience, and base_url "
                "must be provided."
            )
        
        self.client_id = client_id or os.getenv("AUTH0_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("AUTH0_CLIENT_SECRET")
        self.auth_base_url = auth_base_url or os.getenv("TOKEN_ENDPOINT")
        self.audience = audience or os.getenv(f"{self.service}_AUDIENCE")
        self.base_url = base_url or str(os.getenv(f"{self.service}_URL"))

        self.token_cache_buffer = token_cache_buffer
        self.cache = self._init_cache(cache)

        super().__init__(
            self.client_id,
            self.client_secret,
            base_url=self.base_url,
            timeout=30,
            event_hooks={"response": [raise_on_4xx_5xx]},
        )
    
    @staticmethod
    def _init_cache(cache=None):
        """Initialise the cache to use for storing tokens"""
        if cache:
            return cache
    
        if os.getenv("MEMCACHED_URL"):
            return Client(os.getenv("MEMCACHED_URL"), serde=serde.pickle_serde)
        
        logging.warning("No cache provided and no MEMCACHED_URL environment variable found. Using InMemoryCache")
        return InMemoryCache()
        
    async def __aenter__(self):
        """Fetch the token when entering a context manager"""
        await self.fetch_token()
        return self

    async def fetch_token(self, *args, **kwargs):
        # Get from memory
        if self.token and not self.token.is_expired():
            logging.info("Using m2m token from memory")
            return self.token
        # Get from cache
        logging.info("No m2m token found in memory. Fetching token from cache")
        key = f"{self.client_id}{self.audience}"
        token = self.cache.get(key)
        if token and not token.is_expired():
            logging.info("Retrieved token from the cache")
            self.token = token
            return token
        # Get from token endpoint
        logging.info("No m2m token found in cache. Fetching token from token endpoint")
        token = await super().fetch_token(
            self.auth_base_url,
            audience=self.audience,
            grant_type="client_credentials",
        )

        # Save the token to the cache
        logging.info("Saving m2m token to cache")

        ttl = token.get("expires_in") - self.token_cache_buffer
        if ttl < 0:
            ttl = token.get("expires_in")
        self.cache.set(key, token, ttl)

        return token


async def raise_on_4xx_5xx(response: httpx.Response) -> None:
    """Always raise for status for 4xx and 5xx status codes"""
    response.raise_for_status()
