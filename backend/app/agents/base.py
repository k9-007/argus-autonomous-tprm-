"""Shared agent context + emit protocol.

Agents are pure functions over a shared `ctx` dict; they report progress through
an `emit(agent, message, status)` callback that the orchestrator persists as the
live activity feed. This keeps agents testable and DB-agnostic.
"""

from __future__ import annotations

from typing import Callable, Protocol

# emit(agent_name, message, status) where status in {info, working, done, warn}
Emit = Callable[[str, str, str], None]


class Agent(Protocol):
    name: str

    def run(self, ctx: dict, emit: Emit) -> None: ...
