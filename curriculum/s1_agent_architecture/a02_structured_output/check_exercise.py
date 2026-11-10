from pydantic import ValidationError
from exercise import solve

def main():
    valid = solve({"arguments_json": '{"topic":"refund"}'})
    assert valid["arguments"] == {"topic": "refund"}
    assert valid["schema"]["additionalProperties"] is False
    for bad in ('{"topic":42}', '{"topic":""}', '{"topic":"refund","admin":true}'):
        try:
            solve({"arguments_json": bad})
        except ValidationError:
            pass
        else:
            raise AssertionError("invalid tool arguments passed")
    print("A02: PASS")

if __name__ == "__main__":
    main()
