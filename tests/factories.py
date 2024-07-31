from polyfactory.factories.pydantic_factory import ModelFactory

from src import schema


class FileTypeFactory(ModelFactory[schema.FileType]):
    __model__ = schema.FileType


class OrganisationFactory(ModelFactory[schema.PageOfOrganisations]):
    __model__ = schema.PageOfOrganisations


class ClaimFactory(ModelFactory[schema.PageOfClaims]):
    __model__ = schema.PageOfClaims
