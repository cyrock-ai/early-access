# Operations

Running the evaluation image beyond a first look: persistence, backup, monitoring and upgrades.

## Storage and volumes

Everything the engine owns lives under `/data` - storage files, indices and the seeded credentials.
Mount a volume there or lose it on container exit:

```bash
-v cyrock-db-data:/data
```

A named volume is the simplest choice. A host directory works too and is easier to back up or inspect:

```bash
-v "$PWD/cyrock-data:/data"
```

The container runs as a non-root user, so a host directory must be writable by it. A named volume
avoids the question entirely, which is why the examples use one.

`/data/bootstrap-state.properties` holds the seeded API key and project ID. It is why a restart keeps
the same credentials - and why deleting it forces a re-seed.

## Backup

Storage is a set of files under `/data`, so a backup is a copy of that directory. Take it with the
container stopped, so no commit is in flight:

```bash
docker stop cyrock-db

docker run --rm \
  -v cyrock-db-data:/data:ro \
  -v "$PWD:/backup" \
  busybox tar czf /backup/cyrock-db-backup.tar.gz -C /data .

docker start cyrock-db
```

Restore into a fresh volume:

```bash
docker run --rm \
  -v cyrock-db-restored:/data \
  -v "$PWD:/backup" \
  busybox tar xzf /backup/cyrock-db-backup.tar.gz -C /data
```

Then run the container against `cyrock-db-restored`. Verify a restore at least once before you rely on
it - an untested backup is a hypothesis.

## Health

Two unauthenticated endpoints, so orchestrators can reach them:

```bash
curl http://localhost:8082/actuator/health
```

```json
{"groups":["liveness","readiness"],"status":"UP"}
```

The image also declares its own `HEALTHCHECK`, so `docker ps` reports `health: starting` and then
`healthy` without you polling anything. First start allows 90 seconds before health is enforced,
because seeding takes 30-60.

The platform server has the same endpoints on `8081`.

## Metrics

Prometheus format, no configuration needed:

```bash
curl http://localhost:8082/actuator/prometheus
```

Alongside JVM and HTTP metrics you get engine-level ones - query latency, index sizes, commit counts.
A minimal scrape config:

```yaml
scrape_configs:
  - job_name: cyrock-db
    metrics_path: /actuator/prometheus
    static_configs:
      - targets: ['localhost:8082', 'localhost:8081']
```

What is worth watching first: **heap used against heap max** (the metric that most often explains a
slowdown in this single-JVM image), **query latency percentiles**, and **storage size on disk**.

For traces, set `OTEL_EXPORTER_OTLP_ENDPOINT` to a collector - see [Configuration](configuration.md).

## Logs

```bash
docker logs cyrock-db              # everything
docker logs -f cyrock-db           # follow
docker logs --tail 200 cyrock-db   # recent
```

The startup banner is at the top of the log, which is where to look for the API key and project ID if
you have lost them:

```bash
# macOS / Linux
docker logs cyrock-db | head -40
```

```powershell
# Windows
docker logs cyrock-db | Select-Object -First 40
```

## Resource sizing

One JVM runs the whole engine here, and vector indices are held in memory for search. Vector count and
dimension drive memory more than document count does.

| Use | Memory | `JAVA_OPTS` |
|---|---|---|
| Sample data, exploring | 4 GB | `-Xmx3g` |
| Tens of thousands of vectors | 8 GB | `-Xmx6g` |
| Hundreds of thousands of vectors | 16 GB | `-Xmx12g` |

Leave headroom - `-Xmx` is the heap, and the JVM needs more than the heap. Setting `-Xmx` above what
Docker will grant moves the failure rather than preventing it, so raise Docker's own memory limit
alongside it.

Disk: storage grows with your data plus index overhead. Vectors dominate - 384 floats per vector is
about 1.5 KB before indexing.

## Upgrading

Early Access releases are tagged. Substitute the tag you are moving to for `<new-version>` below, then
pull it and restart against the same volume:

```bash
docker stop cyrock-db && docker rm cyrock-db
docker pull cyrockai/db:<new-version>
docker run -d --name cyrock-db \
  -p 8080:8080 -p 8081:8081 -p 8082:8082 -p 8085:8085 -p 9090:9090 \
  -v cyrock-db-data:/data -e JAVA_OPTS=-Xmx6g \
  cyrockai/db:<new-version>
```

Take a backup first. Storage carries over between Early Access releases, but this is pre-release
software and a rollback is only as good as your last copy.

Pin an exact version rather than tracking `latest`, so an upgrade is something you choose. Note that
`latest` will eventually cross from Early Access to general availability, which is a change of licence
terms as well as of version - another reason to pin.

## Stopping

Give it a longer grace period than Docker's default:

```bash
docker stop -t 60 cyrock-db
```

`stop` sends `SIGTERM`, which reaches the JVM directly - the entrypoint runs it as PID 1. The engine
then drains in-flight requests, flushes the vector indices and closes storage, which takes **around 40
seconds**. Docker's default grace period is 10, so a plain `docker stop` sends `SIGKILL` partway
through and the container exits 137.

That is not as bad as it sounds: every statement commits atomically, so data written before the stop is
already durable and a killed shutdown loses nothing. You will simply see a `137` exit and no clean
shutdown in the log. Passing `-t 60` lets it finish properly and exit `143`.

Confirm a clean shutdown in the log:

```bash
# macOS / Linux
docker logs cyrock-db 2>&1 | grep "Storage system stopped"
```

```powershell
# Windows
docker logs cyrock-db 2>&1 | Select-String "Storage system stopped"
```

One thing to avoid: stopping while the container is still starting. The health status turns `healthy`
once the engine and the MCP endpoint are up, so wait for that before stopping - a `SIGTERM` that lands
mid-startup produces a `Shutdown in progress` stack trace in the log. It is harmless, and no data is at
risk, but it looks alarming.
