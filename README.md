<h2 align="center">Microservice Rest Client</h2>

POC for a microservice rest client that can be used to handle machine to machine communication between microservices.

## Example Usage

### Creating a client

There are a few different ways that you can create a client. The simplest way is to create a client using the `M2MClient` class.
```python
from src.client import M2MClient
client = M2MClient(service="data-catalogue")
```
With this method, you only need to specify the name of the service that you want to communicate with. The remaining configuration will 
be read from the environment variables.

If you don't have those environment variables configured, you can specify the configuration manually.
```python
from src.client import M2MClient
client = M2MClient(
        client_id="client_id",
        client_secret="client_secret",
        #...
)
```
If you use either of these methods to create the client, you will need to manually fetch the access token and should also close the client
when you are done with it:
```python
from src.client import M2MClient

async def main():
    client = M2MClient(service="data-catalogue")
    await client.fetch_token()
    # Do something with the client
    await client.aclose()
```
For convenience, there is also an asyncronous context manager that will handle all of this for you:
```python
from src.utilities import get_client

async def main():
    async with get_client("data-catalogue") as client:
        # Do something with the client
```

### Making a request

Once you have a client, you can use it to make requests to the service that it is configured to communicate with. The client can be
used just like a httpx client, with the added bonus that you don't need to specify the base url for the service that you are communicating with.
```python
from src.utilities import get_client

async def main():
    async with get_client("authinator") as client:
        response = await client.get("claims")
        print(response.json())
```

There are also some pre-configured functions that can be used to make requests to the service. These functions are decorated with 
the `@inject_client` decorator and will automatically inject the client into the function when it is called.
```python
from src.services import authinator

async def main():
    claims = await authinator.get_claims()
    print(claims)
```

If you already have a client instance, you can also pass that to the function as a keyword argument. This is good practice if 
you are making multiple requests to the same service in quick succession.
```python
from src.services import authinator
from src.utilities import get_client

async def main():
    async with get_client("authinator") as client:
        await authinator.get_claims(client=client, page=1)
        await authinator.get_claims(client=client, page=2)
```

### Pagination

If the endpoint that you are calling supports pagination, you can use the `Paginator` class to iterator over pages.
```python
from src.services import authinator
from src.utilities import get_client, Paginator

async def main():
    async with get_client("authinator") as client:
        # Iterate over all pages
        paginator = Paginator(authinator.get_claims, client=client, per_page=100)
        async for page in paginator:
            print(page)

        # Fetch a specific page
        page = await paginator.get(page=2)
        print(page)
```

If you want to just fetch all pages at once, you can use the `fetch_all` method.
```python
from src.services import authinator
from src.utilities import get_client, fetch_all

async def main():
    async with get_client("authinator") as client:
        results = await fetch_all(authinator.get_claims, client=client, per_page=100)
        print(results)
```