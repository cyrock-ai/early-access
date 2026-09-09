# CYROCK.AI DB Python Client

Python client library for the CYROCK.AI DB unified AI data engine. Wraps the gRPC stubs in a clean,
domain-typed API and handles authentication (API key with automatic JWT token exchange).

Every operation comes in two forms: `CyrockDbClient` blocks, and `AsyncCyrockDbClient` is awaited.
See [Asynchronous API](#asynchronous-api).

> For the feature-level overview of the API surface, see [APIs & SDKs](../docs/reference/api-and-sdk.md).
> The Java client is documented in [client-java](../client-java/README.md); the two are meant to be
> the same API, and [Differences from the Java client](#differences-from-the-java-client) lists every
> place they are not.

## Status

Feature-complete against the Java client: 72 operations on each facade, and a reflective test that
fails the build if the two drift.

The unit suite runs against an in-process gRPC server, covering the wire encoding and the client's
behaviour without needing a JVM; `integration/` runs the same operations against a real server started
from the `Bootstrap` harness, and is gated behind `CYROCK_IT=1` so it never runs by accident.

## Installation

The Early Access packages are not on PyPI. Install from the early-access repository, pinned to a tag:

```bash
pip install "git+https://github.com/cyrock-ai/early-access@db-v0.9.1#subdirectory=db-client-python"
```

This needs a GitHub account with access to that repository, the same gate the Maven artifacts sit
behind. Pin a tag rather than a branch, so an install is reproducible.

Both names carry the `db-` prefix because that repository hosts another product too. The published
copy is written there by `release-early-access.yml`, which generates `_proto/` and `_version.py` -
gitignored here, tracked there, because a git install builds the sdist on the consumer's machine where
`proto/src/main/proto` does not exist - stages the tree without `integration/`, installs it into a
clean environment and runs its suite there to prove the copy is neither empty nor broken, and only
then pushes the tag. The default branch of that
repository is never written to; the tag is the artifact.

The generated protobuf modules are compiled against **protobuf 6.31.1** and **grpcio 1.74.0**, which
are the minimums a consumer may hold them to: a newer runtime is fine, an older one refuses to load
the generated code.

> The Java client documents its floor as protobuf **4.31.1**. That is the same protobuf release -
> 31.1 - not a different one. Protobuf versions its language runtimes on separate major lines:
> `protobuf-java` 4.31.1 and the `protobuf` PyPI package 6.31.1 ship from one release. Python has no
> 4.31.1 at all, so do not copy the Java number into a requirements file.

## Quick start

```python
from cyrock_db import CyrockDbClient
from cyrock_db.types import CollectionDefinition, VectorFieldDefinition

with CyrockDbClient(host="localhost", port=9090, api_key="your-api-key") as client:
    collection = client.create_collection(
        project_id,
        CollectionDefinition(
            name="documents",
            vector_fields=(VectorFieldDefinition(name="embedding", dimension=384),),
        ),
    )
    print(collection.id)
```

## Options

Java exposes these through a fluent builder; Python takes them as keyword arguments. Same knobs,
same defaults.

| Option | Default | Meaning |
|---|---|---|
| `host` | `"localhost"` | Hostname or IP |
| `port` | `9090` | gRPC port - a gateway fronting both planes, see below |
| `use_plaintext` | `True` | `False` for TLS |
| `api_key` | `None` | Exchanged for a short-lived JWT and attached to every call |
| `channel_credentials` | `None` | Custom credentials, e.g. mutual TLS. Takes precedence over `use_plaintext` |
| `call_timeout` | `None` | Seconds a single request may take. Per request, not a lifetime budget |
| `keepalive_time` | `None` | Seconds idle before an HTTP/2 keep-alive ping |
| `keepalive_timeout` | `None` | Seconds to wait for that ping to be answered |
| `max_inbound_message_size` | gRPC default (4 MiB) | Bytes |

When an API key is provided, the client exchanges it for a short-lived JWT via `TokenGrpcService` and
attaches that token to subsequent calls.

**Which endpoint to use.** The client sends both platform-plane and data-plane calls over one
channel - the API-key exchange is on the platform plane, everything else on the data plane - so the
endpoint has to front both:

| Target | Endpoint | Notes |
|---|---|---|
| All-in-one environment | `localhost:9090` | The client gateway, which merges the two planes. Also the default |
| Composed deployment | the Envoy gateway, `:8000` | Routes both planes by proto package. See [deploy/README.md](../deploy/README.md) |

A bare data-server port (`9092`) is **not** a usable target: it serves the data plane only, so the
client connects and then fails during the API-key exchange rather than at connect time.

## Asynchronous API

`AsyncCyrockDbClient` offers the same operations, awaited:

```python
import asyncio
from cyrock_db.aio import AsyncCyrockDbClient

async def main():
    async with AsyncCyrockDbClient(api_key="your-api-key") as client:
        collections = await asyncio.gather(
            *(client.list_collections(project_id) for project_id in project_ids)
        )

asyncio.run(main())
```

It does not make a single call faster. It buys **concurrency without threads**: the blocking client
parks a thread for every round trip, so fifty calls at once wants fifty threads doing nothing but
waiting; here they are in flight on one connection and none waits.

| | |
|---|---|
| **Parity** | Every `CyrockDbClient` operation has a twin. `tests/test_parity.py` fails the build if the two drift, in either direction |
| **Ordering** | Two coroutines started together have no order - a read fired alongside its own write may not see it. Await the first before starting the second when the order is the point |
| **Failures** | The same exception types the blocking client raises, for the same failures |
| **Where it helps** | Reads and searches gain: the server takes a read lock per store and reads run in parallel. Per-collection write leases bound write throughput server-side, so fanning writes out mostly moves the queue from the client to the server |
| **Change streams** | The one place the two differ in shape. `watch_graph` blocks-and-calls-back on the synchronous client and returns an async iterator on this one; see below |

## Error handling

Every exception extends `CyrockDbClientException`, which carries an **HTTP** status code - never the
gRPC wire ordinal.

| Exception | Status | Raised when |
|---|---|---|
| `NotFoundException` | 404 | The resource does not exist |
| `ForbiddenException` | 403 | Permissions do not cover the request |
| `UnauthorizedException` | 401 | Not authenticated |
| `UnavailableException` | 503 | Server unreachable or not accepting requests |
| `DeadlineExceededException` | 504 | The call did not finish within its deadline |
| `DurabilityNotConfirmedException` | 409 | The write committed and is visible, but the durability flush did not confirm. **Do not retry** - the commit stands |

`UnavailableException` and `DeadlineExceededException` share the base `RetryableException`. Catch
that rather than comparing status codes: the arithmetic is easy to get wrong in the direction that
never retries. 429 is deliberately not retryable - it is the server asking for less load, not for the
same request again.

```python
from cyrock_db import RetryableException

try:
    client.list_collections(project_id)
except RetryableException:
    ...  # worth another attempt
except CyrockDbClientException as error:
    print(error.status_code)
```

## Differences from the Java client

Three, each forced rather than chosen:

1. **No `.async()`.** Java reaches its asynchronous face through `client.async()`, sharing one
   channel and one `close()`. `grpc.Channel` and `grpc.aio.Channel` are separate objects and an aio
   channel must be created on the running event loop, so `AsyncCyrockDbClient` is constructed and
   closed on its own.
2. **Credentials travel by interceptor, not call credentials.** grpc-python refuses a call credential
   on an insecure channel, where grpc-java applies one over plaintext. Since the default target is a
   plaintext gateway, the headers are set by a client interceptor instead. Same headers.
3. **No client-side CyQL parsing.** The Java client parses a statement to reject a write sent to
   `query()` before it leaves. Python sends it and lets the server answer. Routing still works: a
   keyword classifier decides project-scoped DDL from the rest, held to the grammar by a fixture the
   `cyql` module and this package both read.
4. **Change streams differ by facade.** `CyrockDbClient.watch_graph` takes a listener and returns a
   reconnecting subscription on a background thread, as Java does.
   `AsyncCyrockDbClient.watch_graph` returns an async iterator instead - the same idea with the
   control inverted, and what a Python caller expects - and does not reconnect. Checkpoint
   `event.lsn` and re-open with `WatchOptions.resume_from(lsn)`.
5. **Change events are domain objects.** Java's `ChangeListener.onChange` receives the generated
   protobuf; this client decodes into a `ChangeEvent` dataclass, because every other response here
   does and `cyrock_db._proto` is private.

One shared wart worth knowing: with an API key configured, an unreachable server surfaces as
`UnauthorizedException` (401), not `UnavailableException` (503), because the token exchange is the
first thing to touch the network and reports every failure as an authentication failure. The Java
client behaves identically.

## Development

```bash
make venv     # virtualenv with the dev dependencies
make proto    # regenerate src/cyrock_db/_proto from ../proto/src/main/proto
make check    # ruff, mypy --strict, pytest
```

`make proto` needs the reactor checkout beside this directory; it also derives the package version
from the root `pom.xml`, so the Python and Java artifacts cannot carry different versions. A
published copy ships the generated modules already.
