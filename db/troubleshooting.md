# Troubleshooting

## The console is not up yet

**First start takes 30 to 60 seconds** while storage is created and the tenant is seeded. A refused
connection in the first half minute is normal.

Rather than guessing, watch the health status:

```bash
docker ps    # STATUS goes "health: starting" -> "healthy"
```

The banner in the log is the definitive signal:

```bash
docker logs -f cyrock-db
```

If it is still not healthy after a couple of minutes, read the log from the top - a failure to bind a
port or to write to `/data` reports itself there.

## "API key not found" - or you have lost it

The key is printed in the startup banner. Recover it without restarting:

```bash
# macOS / Linux
docker logs cyrock-db | head -40
```

```powershell
# Windows
docker logs cyrock-db | Select-Object -First 40
```

Or read it from the storage directory, where it is cached:

```bash
docker exec cyrock-db cat /data/bootstrap-state.properties
```

If you started **without** a volume, every run seeds a new key, so a key from an earlier run will not
work. Mount `-v cyrock-db-data:/data` to keep credentials stable.

## REST calls suddenly return 401

Tokens last **300 seconds**. A call that worked a few minutes ago and now returns 401 has an expired
token - exchange the API key again:

```bash
TOKEN=$(curl -sS -X POST http://localhost:8081/api/v1/token \
  -H "X-API-Key: $API_KEY" | jq -r .token)
```

Note the exchange is on port **8081**, the platform port, even for data operations on 8082.

A `403` is different: the credential is valid but its role does not permit the operation.

## Out of memory

Symptoms: the container exits unexpectedly, or queries get progressively slower and then fail. Confirm
in the log:

```bash
# macOS / Linux
docker logs cyrock-db 2>&1 | grep -i "OutOfMemory"
```

```powershell
# Windows
docker logs cyrock-db 2>&1 | Select-String "OutOfMemory"
```

The `2>&1` matters here: the JVM reports an `OutOfMemoryError` on stderr, not stdout, so a filter
without it finds nothing and the problem looks like something else.

Raise the heap, and Docker's own limit with it:

```bash
docker run --rm --name cyrock-db --memory=8g -e JAVA_OPTS="-Xmx6g" ... cyrockai/db:0.9.1
```

`-Xmx` above what Docker will grant does not help - the container gets killed instead of the JVM
reporting a clean error. See the sizing table in [Operations](operations.md).

## Port conflicts

`docker run` fails with "port is already allocated". Find the occupant:

```bash
# macOS / Linux
lsof -i :8080
```

```powershell
# Windows
netstat -ano | findstr :8080
```

Either free it, or publish to a different host port - the left-hand number is yours to choose:

```bash
docker run --rm --name cyrock-db -p 18080:8080 -p 18085:8085 ... cyrockai/db:0.9.1
```

The console is then on `http://localhost:18080`, and the MCP endpoint on `http://localhost:18085/mcp`.
Remember to update your MCP client configuration to match.

Ports used: `8080` console, `8081` platform REST, `8082` data REST, `8085` MCP, `9090` client gateway.

## Apple Silicon and ARM

The image is multi-architecture, so it runs natively on Apple Silicon with no emulation and no
`--platform` flag. If you see a warning about platform mismatch, you have probably pinned
`--platform linux/amd64` somewhere - remove it.

## The Java SDK cannot connect

Check, in order:

1. **Is `9090` published?** It is separate from the console port: `-p 9090:9090`.
2. **Are you overriding the port?** You should not need to call `.port(...)` at all - the default
   `9090` is the client gateway. If you have set it to `9092`, that is the data-plane port, and the
   key exchange will fail there.
3. **Is the key current?** A key from a previous volume-less run is gone.

A failure during the key exchange rather than at connect time usually means point 2.

## Protobuf gencode/runtime mismatch on the first generated class

```
com.google.protobuf.RuntimeVersion$ProtobufRuntimeVersionException: Detected incompatible
Protobuf Gencode/Runtime versions when loading ProjectIdRequest: gencode 4.31.1, runtime 4.29.3.
Runtime version cannot be older than the linked gencode version.
```

Your build holds `com.google.protobuf:protobuf-java` at a version older than the one the SDK's
classes were generated against. Protobuf accepts a runtime newer than its generated code but never
an older one, so it refuses while the class is initializing rather than failing later on the wire.
Nothing is wrong with the connection or the key.

Read the two numbers in the message and raise `protobuf-java` to at least the `gencode` one. A
version your build manages always wins over the one the SDK asks for, so the pin has to move where
it actually lives. On Spring Boot 4.1 and later that is a property. Any version at or above the
`gencode` number in your message will do; 4.35.1 below is what the SDK resolves when nothing holds
it back, so it clears the floor with room to spare:

```xml
<properties>
    <protobuf-java.version>4.35.1</protobuf-java.version>
</properties>
```

Elsewhere, declare `com.google.protobuf:protobuf-java` among your own dependencies - a direct
declaration beats one inherited through the SDK - or manage it in `dependencyManagement`. Your
build's dependency tree will show which version you are really resolving and what is asking for the
old one. Importing the [SDK BOM](java-sdk.md) sets a consistent version for you.

A different wording, **"Same major version is required"**, means something is holding Protobuf on
3.x. The SDK needs Protobuf 4.x; the usual culprit is an older gRPC or framework BOM imported ahead
of everything else.

**From Python** the same check exists and reads almost the same: a `VersionError` raised while
importing `cyrock_db`, naming a `gencode` and a `runtime` version. Raise the `protobuf` package to at
least the `gencode` number - `pip install --upgrade protobuf` - and check nothing else in the
environment pins it lower.

Do not copy the Java number across when you do: the Python SDK's floor is Protobuf **6.31.1** and the
Java SDK's is **4.31.1**, and those are the same Protobuf release. Protobuf numbers its language
runtimes on separate major lines, and there is no 4.31.1 on PyPI to install. See
[Python SDK](python-sdk.md).

## MCP tools do not appear in the client

Check the endpoint directly:

```bash
curl -sS -X POST http://localhost:8085/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"curl","version":"1"}}}'
```

A JSON result containing `serverInfo` means the server is fine and the problem is in the client
configuration - most often a missing `Authorization` header or the wrong URL. The path is `/mcp`.

## Vector search returns nothing, or an error about dimensions

Three usual causes:

- **The embedder was turned off.** The image embeds in-process by default, so this only applies if you
  passed `CYROCK_DB_EMBEDDING_ONNX_ENABLED=false` - then a field with no supplied vector has nothing to
  embed it. See [Configuration](configuration.md).
- **Dimension mismatch.** The provider's output length must equal the field's declared dimensions. The
  in-process ONNX model is 384. Changing provider usually changes dimension, which means re-embedding.
- **Your own provider is being ignored.** ONNX takes precedence over the others and is on by default, so
  an Ollama or OpenAI setting does nothing until you set `CYROCK_DB_EMBEDDING_ONNX_ENABLED=false`.

## `LOAD CSV` cannot find the file

Filenames are resolved **relative to** the configured import directory, and cannot escape it. So:

- Mount the directory: `-v "$PWD/imports:/imports:ro"`
- Point the engine at it: `-e CYROCK_DB_DATA_IMPORT_PATH=/imports`
- Refer to the file by name only: `FROM 'movies.csv'`, not an absolute path.

Absolute paths, `..` and symlinks leading out of the directory are rejected by design.

## Data disappeared after a restart

Almost always a missing volume. Without `-v cyrock-db-data:/data` the container is a fresh environment
every time - and `docker run --rm` removes it on exit. Add the volume.

## "Incompatible storage" at startup

The log shows an `INCOMPATIBLE STORAGE` banner, the health endpoint reports storage `DOWN`, and requests
fail with a message like *"The storage at ... was written with format version 1 ... and cannot be read by
this build ... Start with an empty storage directory."*

Your `/data` volume was written by an earlier release whose on-disk format this build cannot read. Early
Access releases may break storage compatibility, and the engine now refuses to serve the old storage at
startup instead of failing later with an obscure error. Start with an empty storage directory: back up the
volume, then remove it and restart on the new version.

```bash
docker stop cyrock-db && docker rm cyrock-db
docker volume rm cyrock-db-data
docker run -d --name cyrock-db \
  -p 8080:8080 -p 8081:8081 -p 8082:8082 -p 8085:8085 -p 9090:9090 \
  -v cyrock-db-data:/data -e JAVA_OPTS=-Xmx6g \
  cyrockai/db:<version>
```

Removing the volume deletes the data it held, so keep the backup until the new version is up and re-seeded.

## Still stuck

Open an [issue](https://github.com/cyrock-ai/early-access/issues) if something is broken, or a
[discussion](https://github.com/cyrock-ai/early-access/discussions) if you are not sure it is. Collect
the log first:

```bash
docker logs cyrock-db > cyrock-db.log 2>&1
```

Please include what you ran, what you expected and what happened. The log's first forty lines carry
the version and configuration, which is usually where the answer is.

Both channels are public, so read the log before attaching it - it contains your API key, and any
project or collection names you have created.
