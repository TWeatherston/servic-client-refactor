import pytest

from src.client import M2MClient
from src.schema import PaginatedResponse
from src.utilities import get_client, inject_client, get_or_create_client, Paginator, fetch_all


@inject_client(service="test")
async def inject_function(client: M2MClient, page: int = 1, per_page: int = 100) -> PaginatedResponse:
    """Function to test client injection."""
    assert isinstance(client, M2MClient)
    assert client.token["access_token"] == "test_access_token"
    return PaginatedResponse(
        items=[f"item_{page}"],
        page=page,
        pages=3,
        per_page=per_page,
    )


@pytest.mark.asyncio
async def test_get_client(client_responses):
    async with get_client(service="test") as client:
        assert isinstance(client, M2MClient)
        assert client.token["access_token"] == "test_access_token"


def test_get_or_create_client_get():
    client = M2MClient(service="test")
    assert get_or_create_client("test", client) == (client, True)


def test_get_or_create_client_create():
    client, inferred = get_or_create_client(service="test")
    assert isinstance(client, M2MClient)
    assert inferred is False


@pytest.mark.asyncio
async def test_inject_client(client_responses):
    await inject_function()

    async with get_client(service="test") as c:
        await inject_function(client=c)


class TestPaginator:
    
    def test_init(self):
        paginator = Paginator(inject_function, per_page=100)
        assert paginator.per_page == 100
        assert paginator.page == 1

    @pytest.mark.asyncio
    async def test_iteration(self, client_responses):
        paginator = Paginator(inject_function, per_page=100)
        async for page in paginator:
            assert isinstance(page, PaginatedResponse)
            assert page.page == paginator.page - 1
            assert page.per_page == paginator.per_page
            assert page.pages == 3
            assert page.items == [f"item_{page.page}"]
            assert page.per_page == 100

    @pytest.mark.asyncio
    async def test_get(self, client_responses):
        paginator = Paginator(inject_function, per_page=100)
        page = await paginator.get(3)
        assert isinstance(page, PaginatedResponse)
        assert page.page == 3
        assert page.per_page == 100
        assert page.pages == 3
        assert page.items == ["item_3"]
        assert page.per_page == 100


@pytest.mark.asyncio
async def test_fetch_all(client_responses):
    async with get_client("test") as client:
        results = await fetch_all(inject_function, client, per_page=100)
        assert results == ['item_1', 'item_2', 'item_3']
