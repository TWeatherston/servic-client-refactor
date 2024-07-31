from ..client import M2MClient
from ..utilities import inject_client
from ..schema import PageOfOrganisations, PageOfClaims
from .service import Service


@inject_client(service=Service.AUTHINATOR)
async def get_organisations(client: M2MClient, **kwargs) -> PageOfOrganisations:
    resp = await client.get("organisations", params=kwargs)
    return PageOfOrganisations(**resp.json())


@inject_client(service=Service.AUTHINATOR)
async def get_claims(client: M2MClient, **kwargs) -> PageOfClaims:
    resp = await client.get("claims", params=kwargs)
    return PageOfClaims(**resp.json())
