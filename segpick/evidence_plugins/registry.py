from __future__ import annotations

from dataclasses import dataclass, field

from .base import EvidenceChannel, EvidencePluginResult


@dataclass(slots=True)
class EvidencePluginRegistry:
    _channels: dict[str, EvidenceChannel] = field(default_factory=dict)

    def register(self, channel: EvidenceChannel) -> None:
        channel_id = channel.channel_id.strip()
        if not channel_id:
            raise ValueError("Evidence channel_id cannot be empty")
        if channel_id in self._channels:
            raise ValueError(f"Evidence channel already registered: {channel_id}")
        self._channels[channel_id] = channel

    def evaluate(self, candidate) -> tuple[tuple[str, EvidencePluginResult], ...]:
        return tuple((channel_id, channel.evaluate(candidate)) for channel_id, channel in self._channels.items())
