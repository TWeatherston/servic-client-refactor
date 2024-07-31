from functools import wraps
from contextlib import asynccontextmanager
from typing import Any, Callable, Coroutine, Optional, cast, AsyncGenerator
import asyncio

from typing_extensions import ParamSpec

from .client import M2MClient
from .schema import PaginatedResponse


P = ParamSpec("P")


@asynccontextmanager
async def async_null_context():
    """Creates a generic async context manager that does nothing."""
    yield


@asynccontextmanager
async def get_client(service: str) -> AsyncGenerator[M2MClient, None]:
    """Context manager for creating a client and fetching a token.

    Args:
        service (str): The service to create a client for.

    Yields:
        M2MClient: The client for the service.
    """
    client = M2MClient(service)
    await client.fetch_token()
    try:
        yield client
    finally:
        await client.aclose()


def get_or_create_client(
    service: str,
    client: Optional[M2MClient] = None,
) -> tuple[M2MClient, bool]:
    """
    Returns provided client, infers a client from context if available, or creates a new client.

    Args:
        - client (PrefectClient, optional): an optional client to use

    Returns:
        - tuple: a tuple of the client and a boolean indicating if the client was inferred from context
    """
    if client is not None:
        return client, True

    return M2MClient(service), False


def inject_client(service: str):
    """
    Simple helper to provide a context managed client to an asynchronous function.

    The decorated function _must_ take a `client` kwarg and if a client is passed when
    called it will be used instead of creating a new one, but it will not be context
    managed as it is assumed that the caller is managing the context.

    Args:
        service (str): The service to create a client for.
    """

    def decorator(
        fn: Callable[P, Coroutine[Any, Any, Any]],
    ) -> Callable[P, Coroutine[Any, Any, Any]]:
        @wraps(fn)
        async def with_injected_client(*args: P.args, **kwargs: P.kwargs) -> Any:
            client = cast(Optional[M2MClient], kwargs.pop("client", None))
            client, inferred = get_or_create_client(service, client)
            if not inferred:
                context = client
            else:
                # If the client was inferred from context, we don't want to close it so open a null context
                context = async_null_context()

            async with context as new_client:
                kwargs.setdefault("client", new_client or client)
                return await fn(*args, **kwargs)

        return with_injected_client

    return decorator


class Paginator:
    """A simple paginator for paginated API responses.

    Args:
        fn (Callable[..., Coroutine[Any, Any, PaginatedResponse]): The async function to call to get a page of results.
        per_page (int): The number of items per page.
    """

    def __init__(
        self,
        fn: Callable[..., Coroutine[Any, Any, PaginatedResponse]],
        *args,
        per_page: int,
        **kwargs,
    ) -> None:
        self.fn = fn
        self.per_page = per_page
        self.page = 1
        self.pages = None
        self.args = args
        self.kwargs = kwargs

    def __aiter__(self) -> "Paginator":
        """Return the paginator as an async iterator."""
        return self

    async def __anext__(self) -> PaginatedResponse:
        """Get the next page of results. This will raise a StopAsyncIteration if there are no more pages.

        Returns:
            PaginatedResponse: A page response from the API
        """
        if self.pages is not None and self.page > self.pages:
            raise StopAsyncIteration

        response = await self.fn(
            *self.args, page=self.page, per_page=self.per_page, **self.kwargs
        )
        self.pages = response.pages
        self.page += 1
        return response

    async def get(self, page: int) -> PaginatedResponse:
        """Get a specific page of results. This will set the current page to the requested page.

        Args:
            page (int): The page to get.

        Returns:
            PaginatedResponse: A page response from the API.
        """
        response = await self.fn(
            *self.args, page=page, per_page=self.per_page, **self.kwargs
        )
        self.pages = response.pages
        self.page = page
        return response


async def fetch_all(
    fn: Callable[..., Coroutine[Any, Any, PaginatedResponse]],
    client: M2MClient,
    *args,
    per_page: int,
    **kwargs,
) -> list:
    """Fetch all pages of a paginated API response.

    Args:
        fn (Callable[..., Coroutine[Any, Any, PaginatedResponse]): The async function to call to get a page of results.
        client (M2MClient): The client to use to make the requests.
        per_page (int): The number of items per page.

    Returns:
        list: A list of all items from all pages.
    """
    first_page = await fn(*args, client=client, page=1, per_page=per_page, **kwargs)

    if first_page.pages == 1:
        return first_page.items

    remaining_pages = await asyncio.gather(
        *[
            fn(*args, client=client, page=i, per_page=per_page, **kwargs)
            for i in range(2, first_page.pages + 1)
        ]
    )
    first_page.items.extend([item for page in remaining_pages for item in page.items])
    return first_page.items
