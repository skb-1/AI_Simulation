"""Background worker streaming LLM generation without blocking the 30 FPS render loop."""

from __future__ import annotations

import queue
import threading
from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from aicreator.llm import CreatorLLM

# Message types for queue
MSG_TOKEN = "TOKEN"
MSG_DONE = "DONE"
MSG_ERROR = "ERROR"


class GenerationWorker:
    """Manages background thread execution for LLM token streaming with manual slots."""

    __slots__ = ("llm", "queue", "_thread", "is_generating", "current_text")

    def __init__(self, llm: CreatorLLM) -> None:
        self.llm = llm
        self.queue: queue.Queue[Tuple[str, str]] = queue.Queue()
        self._thread: threading.Thread | None = None
        self.is_generating = False
        self.current_text = ""

    def start(self, user_prompt: str) -> bool:
        """Start streaming generation in background thread."""
        if self.is_generating:
            return False

        self.is_generating = True
        self.current_text = ""
        # Drain any leftover messages in queue
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except queue.Empty:
                break

        self._thread = threading.Thread(
            target=self._run_generation,
            args=(user_prompt,),
            daemon=True,
        )
        self._thread.start()
        return True

    def _run_generation(self, user_prompt: str) -> None:
        """Worker thread function."""
        accumulated: list[str] = []
        try:
            for token in self.llm.stream_generate(user_prompt):
                accumulated.append(token)
                self.queue.put((MSG_TOKEN, token))
            full_text = "".join(accumulated)
            self.queue.put((MSG_DONE, full_text))
        except Exception as exc:
            self.queue.put((MSG_ERROR, str(exc)))
        finally:
            self.is_generating = False

    def poll(self) -> list[Tuple[str, str]]:
        """Poll queued generation messages non-blockingly."""
        messages: list[Tuple[str, str]] = []
        while True:
            try:
                msg = self.queue.get_nowait()
                messages.append(msg)
                if msg[0] == MSG_TOKEN:
                    self.current_text += msg[1]
            except queue.Empty:
                break
        return messages
