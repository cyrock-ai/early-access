"""Connection settings, and the channel they build.

Mirrors ``CyrockDbClientGrpc.Builder`` and its ``newChannelBuilder`` / ``applyChannelOptions``. Java
exposes these through a fluent builder; Python takes them as keyword arguments, which is the same
set of knobs with the same defaults and one less type to learn.

The one option that is not a channel option is ``call_timeout``. Java installs a
``CallDeadlineInterceptor`` because a deadline set on a stub is an absolute instant, fixed when the
stub is built, so a long-lived client would see every call after the first few minutes fail
immediately. grpc-python takes a per-call ``timeout`` in seconds instead, which is relative and has
no such trap - so the facades pass it on each unary call and leave streaming calls alone. A Change
Data Capture subscription is meant to stay open; a request timeout on it would tear the stream down
on a schedule and the reconnect loop would look like a flapping server.
"""

from __future__ import annotations

from dataclasses import dataclass

import grpc

__all__ = ["ClientOptions"]

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 9090


def _checked_timeout(name: str, value: float | None) -> float | None:
    if value is None:
        return None
    if value <= 0:
        raise ValueError(f"{name} must be positive, was {value}")
    return value


@dataclass(frozen=True)
class ClientOptions:
    """How to reach the server, and how calls on that connection behave.

    ``port`` defaults to 9090, the client gateway that fronts both planes. That default matters: the
    client sends platform-plane calls (the API-key exchange) and data-plane calls over one channel,
    so a bare data-server port such as 9092 is not a usable target - it serves the data plane only,
    and the client connects successfully and then fails during the key exchange rather than at
    connect time.

    :param host: hostname or IP (default ``localhost``)
    :param port: gRPC port (default 9090)
    :param use_plaintext: ``True`` for plaintext, ``False`` for TLS (default ``True``)
    :param api_key: exchanged for a short-lived JWT and attached to every call; ``None`` for
        unauthenticated access
    :param channel_credentials: custom credentials, e.g. mutual TLS. Takes precedence over
        ``use_plaintext``
    :param call_timeout: seconds a single request may take before it fails with
        ``DeadlineExceededException``. Per request, not a budget for the client's lifetime. Change
        Data Capture subscriptions are exempt. ``None`` for none, the default
    :param keepalive_time: seconds the channel stays idle before sending an HTTP/2 keep-alive ping.
        Worth setting when the connection crosses a load balancer or NAT that drops idle connections
        silently: without a ping, the client discovers the connection is gone only when a request
        fails on it
    :param keepalive_timeout: seconds to wait for a keep-alive ping to be answered before treating
        the connection as dead
    :param max_inbound_message_size: bytes; 0 leaves the gRPC default of 4 MiB
    """

    host:                    str                            = DEFAULT_HOST
    port:                    int                            = DEFAULT_PORT
    use_plaintext:           bool                           = True
    api_key:                 str | None                     = None
    channel_credentials:     grpc.ChannelCredentials | None = None
    call_timeout:            float | None                   = None
    keepalive_time:          float | None                   = None
    keepalive_timeout:       float | None                   = None
    max_inbound_message_size: int                           = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "call_timeout",      _checked_timeout("call_timeout", self.call_timeout))
        object.__setattr__(self, "keepalive_time",    _checked_timeout("keepalive_time", self.keepalive_time))
        object.__setattr__(self, "keepalive_timeout", _checked_timeout("keepalive_timeout", self.keepalive_timeout))
        if self.max_inbound_message_size < 0:
            raise ValueError(f"max_inbound_message_size must not be negative, was {self.max_inbound_message_size}")

    @property
    def target(self) -> str:
        return f"{self.host}:{self.port}"

    def channel_arguments(self) -> list[tuple[str, int]]:
        """The gRPC channel arguments these settings imply."""
        arguments: list[tuple[str, int]] = []
        if self.keepalive_time is not None:
            arguments.append(("grpc.keepalive_time_ms", int(self.keepalive_time * 1000)))
        if self.keepalive_timeout is not None:
            arguments.append(("grpc.keepalive_timeout_ms", int(self.keepalive_timeout * 1000)))
        if self.max_inbound_message_size > 0:
            arguments.append(("grpc.max_receive_message_length", self.max_inbound_message_size))
        return arguments

    def credentials(self) -> grpc.ChannelCredentials | None:
        """The credentials to build a channel with, or ``None`` to build an insecure one."""
        if self.channel_credentials is not None:
            return self.channel_credentials
        return None if self.use_plaintext else grpc.ssl_channel_credentials()
