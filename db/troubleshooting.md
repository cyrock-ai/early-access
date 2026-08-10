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
docker run --rm --name cyrock-db --memory=8g -e JAVA_OPTS="-Xmx6g" ... cyrockai/db:0.9.0
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
docker run --rm --name cyrock-db -p 18080:8080 -p 18085:8085 ... cyrockai/db:0.9.0
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

- **No embedding provider and no supplied vectors.** Turn on the in-process embedder with
  `CYROCK_DB_EMBEDDING_ONNX_ENABLED=true` - it needs no account and no network. See
  [Configuration](configuration.md).
- **Dimension mismatch.** The provider's output length must equal the field's declared dimensions. The
  in-process ONNX model is 384. Changing provider usually changes dimension, which means re-embedding.
- **Several providers configured.** ONNX takes precedence over all the others when enabled, so an
  Ollama or OpenAI setting is silently ignored while it is on.

## `LOAD CSV` cannot find the file

Filenames are resolved **relative to** the configured import directory, and cannot escape it. So:

- Mount the directory: `-v "$PWD/imports:/imports:ro"`
- Point the engine at it: `-e CYROCK_DB_DATA_IMPORT_PATH=/imports`
- Refer to the file by name only: `FROM 'movies.csv'`, not an absolute path.

Absolute paths, `..` and symlinks leading out of the directory are rejected by design.

## Data disappeared after a restart

Almost always a missing volume. Without `-v cyrock-db-data:/data` the container is a fresh environment
every time - and `docker run --rm` removes it on exit. Add the volume.

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
