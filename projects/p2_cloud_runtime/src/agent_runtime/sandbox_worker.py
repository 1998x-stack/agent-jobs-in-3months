"""Fixed, no-third-party-dependency subprocess workload for B09.

NO user-supplied code, shell commands, filesystem paths, network actions or
arbitrary tool names. Supervisor passes a bounded JSON object on stdin.
"""
import hashlib
import json
import os
import sys


def main() -> None:
    if os.name == "posix":
        import resource
        resource.setrlimit(resource.RLIMIT_CPU, (3, 3))
        memory = int(os.environ["AGENT_WORKER_MEMORY_MB"]) * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
        resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024, 1024 * 1024))
        os.umask(0o077)
    request = json.load(sys.stdin)
    operation = request["operation"]
    payload = request["text"]
    if operation == "hash_text":
        result = {"sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest()}
    elif operation == "count_words":
        result = {"word_count": len(payload.split())}
    else:
        raise ValueError("operation is not allowlisted")
    print(json.dumps(result, separators=(",", ":")))


if __name__ == "__main__":
    main()
