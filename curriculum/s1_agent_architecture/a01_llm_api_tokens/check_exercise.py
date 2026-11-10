from exercise import solve

def main():
    result = solve({"goal": "Check refund policy", "max_output_tokens": 96})
    assert result["messages"] == [{"role": "user", "content": "Check refund policy"}]
    assert result["max_output_tokens"] == 96
    for data in ({"goal": ""}, {"goal": "x", "max_output_tokens": -1}):
        try:
            solve(data)
        except ValueError:
            pass
        else:
            raise AssertionError("bad request was accepted")
    print("A01: PASS")

if __name__ == "__main__":
    main()
