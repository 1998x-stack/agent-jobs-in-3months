import hashlib
from exercise import solve


def main() -> None:
    assert solve({"operation": "hash_text", "data": "hello"})["sha256"] == (
        hashlib.sha256(b"hello").hexdigest()
    )
    for invalid in (
        {"operation": "shell", "data": "hi"},
        {"operation": "hash_text", "data": "hi", "command": "rm -rf"},
        {"operation": "hash_text", "data": "x" * 1000},
    ):
        try:
            solve(invalid)
        except (ValueError, PermissionError):
            pass
        else:
            raise AssertionError("unbounded operation accepted")
    print("B09: PASS")


if __name__ == "__main__":
    main()
