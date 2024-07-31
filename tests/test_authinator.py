import pytest

from src.services import authinator
from .factories import OrganisationFactory, ClaimFactory


@pytest.mark.asyncio
async def test_get_organisations(client_responses):
    organisation = OrganisationFactory.build()
    client_responses.add_response(
        url="https://authinator.test.com/organisations",
        method="GET",
        json=organisation.model_dump(),
    )
    response = await authinator.get_organisations()
    assert response == organisation


@pytest.mark.asyncio
async def test_get_claims(client_responses):
    claims = ClaimFactory.build()
    client_responses.add_response(
        url="https://authinator.test.com/claims",
        method="GET",
        json=claims.dict(),
    )
    response = await authinator.get_claims()
    assert response == claims
