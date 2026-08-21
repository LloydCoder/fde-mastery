"""SSRF-aware outbound HTTP boundary for integration adapters."""
from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(frozen=True, slots=True)
class OutboundURLPolicy:
    allowed_hosts: frozenset[str]
    allow_private_networks: bool = False

    def validate(self, url: str) -> None:
        parsed = urlsplit(url)
        if parsed.scheme not in {"https"}:
            raise ValueError("integration endpoints must use HTTPS")
        if parsed.username or parsed.password:
            raise ValueError("URL credentials are not permitted")
        hostname = (parsed.hostname or "").rstrip(".").lower()
        if not hostname:
            raise ValueError("URL hostname is required")
        if hostname not in {host.lower().rstrip(".") for host in self.allowed_hosts}:
            raise PermissionError("integration endpoint host is not allowlisted")
        if not self.allow_private_networks:
            self._reject_private_resolution(hostname)

    @staticmethod
    def _reject_private_resolution(hostname: str) -> None:
        if hostname in {"localhost", "localhost.localdomain"}:
            raise PermissionError("private or loopback integration targets are blocked")
        try:
            addresses = {item[4][0] for item in socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)}
        except socket.gaierror as exc:
            raise ValueError("integration endpoint hostname cannot be resolved") from exc
        for raw in addresses:
            try:
                address = ipaddress.ip_address(raw)
            except ValueError as exc:
                raise ValueError("integration endpoint resolved to an invalid IP address") from exc
            if address.is_private or address.is_loopback or address.is_link_local or address.is_reserved or address.is_multicast:
                raise PermissionError("integration endpoint resolves to a private or reserved network")
            if str(address) in {"169.254.169.254", "100.100.100.200"}:
                raise PermissionError("cloud metadata endpoints are blocked")


class OutboundHTTPClient:
    """Small adapter boundary; callers must validate the endpoint before sending."""

    def __init__(self, policy: OutboundURLPolicy, transport) -> None:
        self.policy = policy
        self.transport = transport

    def request(self, method: str, url: str, **kwargs):
        self.policy.validate(url)
        kwargs.setdefault("timeout", 10)
        kwargs.setdefault("allow_redirects", False)
        return self.transport.request(method, url, **kwargs)
