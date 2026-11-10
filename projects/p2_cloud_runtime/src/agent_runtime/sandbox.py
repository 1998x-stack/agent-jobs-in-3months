"""B09: narrow subprocess containment for two allowlisted pure functions.

Python -I -S, empty environment, temporary cwd, execution timeout, and
Linux/POSIX resource caps. This DOES NOT provide a kernel security boundary,
network namespace, seccomp, container sandbox, or safe arbitrary code execution.
The child source code is fixed and trusted; never accept arbitrary commands.
"""
from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
import sys
import tempfile


_OPERATIONS = frozenset({"hash_text", "count_words"})


class SandboxViolation(ValueError):
    """Disallowed input, tool or sandbox execution failure."""


@dataclass(frozen=True)
class SandboxPolicy:
    timeout_seconds: float = 2.0
    max_input_chars: int = 512
    max_output_bytes: int = 4096
    max_memory_mb: int = 128

    def __post_init__(self) -> None:
        if not 0 < self.timeout_seconds <= 10:
            raise ValueError("timeout must be (0,10] seconds")
        if type(self.max_input_chars) is not int or not 1 <= self.max_input_chars <= 4096:
            raise ValueError("invalid max input chars")
        if type(self.max_output_bytes) is not int or not 64 <= self.max_output_bytes <= 8192:
            raise ValueError("invalid max output bytes")
        if type(self.max_memory_mb) is not int or not 64 <= self.max_memory_mb <= 256:
            raise ValueError("invalid memory limit")


class SandboxRunner:
    def __init__(self, policy: SandboxPolicy | None = None) -> None:
        self.policy = policy or SandboxPolicy()

    def run(self, operation: str, text: str) -> dict:
        if operation not in _OPERATIONS:
            raise SandboxViolation("operation not allowlisted")
        if not isinstance(text, str) or not text or len(text) > self.policy.max_input_chars:
            raise SandboxViolation("invalid or oversized input")
        command = [
            sys.executable, "-I", "-S",
            str(Path(__file__).resolve().with_name("sandbox_worker.py")),
        ]
        payload = json.dumps({"operation": operation, "text": text})
        env = {
            "PYTHONIOENCODING": "utf-8",
            "PYTHONDONTWRITEBYTECODE": "1",
            "AGENT_WORKER_MEMORY_MB": str(self.policy.max_memory_mb),
        }
        try:
            with tempfile.TemporaryDirectory(prefix="agent-b09-") as cwd:
                result = subprocess.run(
                    command,
                    input=payload,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,  # Do not leak input/tracebacks.
                    text=True,
                    timeout=self.policy.timeout_seconds,
                    cwd=cwd,
                    env=env,
                    check=False,
                    start_new_session=True,
                    close_fds=True,
                )
        except (subprocess.TimeoutExpired, OSError) as exc:
            raise SandboxViolation("sandbox timeout or launch failure") from exc
        if result.returncode != 0 or len(result.stdout.encode()) > self.policy.max_output_bytes:
            raise SandboxViolation("sandbox process failed or exceeded output limit")
        try:
            data = json.loads(result.stdout)
        except (ValueError, TypeError) as exc:
            raise SandboxViolation("sandbox returned invalid JSON") from exc
        if not isinstance(data, dict) or set(data) != (
            {"sha256"} if operation == "hash_text" else {"word_count"}
        ):
            raise SandboxViolation("sandbox output contract rejected")
        return data
