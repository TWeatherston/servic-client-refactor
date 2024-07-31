import pytest

from src.services import data_catalogue
from .factories import FileTypeFactory


@pytest.mark.asyncio
async def test_get_file_type(client_responses):
    file_type = FileTypeFactory.build()
    client_responses.add_response(
        url="https://data-catalogue.test.com/file_types?feed_identifier=test&feed_version=1",
        method="GET",
        json=file_type.dict(),
    )
    response = await data_catalogue.get_file_type(feed_identifier="test", feed_version=1)
    assert response == file_type

