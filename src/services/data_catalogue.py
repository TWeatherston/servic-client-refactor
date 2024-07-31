from typing import IO, AnyStr

import httpx

from ..client import M2MClient
from ..utilities import inject_client
from ..schema import FileType, SignedURL, FileRecord
from .service import Service


@inject_client(service=Service.DATA_CATALOGUE)
async def get_file_type(
    client: M2MClient, feed_identifier: str, feed_version: int
) -> FileType:
    resp = await client.get(
        "file_types",
        params={"feed_identifier": feed_identifier, "feed_version": feed_version},
    )
    return FileType(**resp.json())


@inject_client(service=Service.DATA_CATALOGUE)
async def get_signed_url(
    client: M2MClient, feed_identifier: str, feed_version: int
) -> SignedURL:
    resp = await client.post(
        "signed_url/",
        json={"feed_identifier": feed_identifier, "feed_version": feed_version},
    )
    return SignedURL(**resp.json())


@inject_client(service=Service.DATA_CATALOGUE)
async def post_file_record(
    client: M2MClient,
    feed_identifier: str,
    feed_version: int,
    file_location: str,
    file_meta: dict,
    organisation: str = "atheon",
) -> FileRecord:
    resp = await client.post(
        "records",
        json={
            "feed_identifier": feed_identifier,
            "feed_version": feed_version,
            "file_location": file_location,
            "organisation": organisation,
            "file_meta": file_meta,
        },
    )
    return FileRecord(**resp.json())


@inject_client(service=Service.DATA_CATALOGUE)
async def upload_and_catalogue_file(
    client: M2MClient,
    file: IO[AnyStr],
    feed_identifier: str,
    feed_version: int,
    file_meta: dict,
) -> FileRecord:
    signed_url = await get_signed_url(
        client=client, feed_identifier=feed_identifier, feed_version=feed_version
    )
    await upload_using_signed_url(file, signed_url)
    return await post_file_record(
        client=client,
        feed_identifier=feed_identifier,
        feed_version=feed_version,
        file_location=signed_url.file_path,
        file_meta=file_meta,
    )


async def upload_using_signed_url(file: IO[AnyStr], signed_url: SignedURL) -> None:
    files = {"file": (signed_url.fields["key"], file)}
    async with httpx.AsyncClient() as client:
        http_response = await client.post(
            signed_url.signed_url, data=signed_url.fields, files=files
        )
        http_response.raise_for_status()
        print("File uploaded successfully")
