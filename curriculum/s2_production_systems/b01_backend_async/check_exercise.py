from fastapi.testclient import TestClient
from exercise import app


def main() -> None:
    with TestClient(app) as client:
        response = client.post("/tasks", json={"question": "refund approval"})
        assert response.status_code == 202
        task_id = response.json()["task_id"]
        assert client.get(f"/tasks/{task_id}").json()["question"] == "refund approval"
        assert client.get("/tasks/missing").status_code == 404
        assert client.post("/tasks", json={"question": "refund", "admin": True}).status_code == 422
    print("B01: PASS")


if __name__ == "__main__":
    main()
