import pytest
from fastapi.testclient import TestClient

from main import app, game


@pytest.fixture
def client():
    game.started = False
    game.game_over = False
    game.reason = None
    game.snake.clear()
    game.food = None
    game.score = 0
    game.steps = 0
    game.direction = "right"
    return TestClient(app)


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_step_before_start_is_conflict(client):
    response = client.post("/step", json={})
    assert response.status_code == 409


def test_unknown_direction_is_bad_request(client):
    client.post("/new")
    response = client.post("/step", json={"direction": "north"})
    assert response.status_code == 400


def test_reverse_is_bad_request(client):
    client.post("/new")
    response = client.post("/step", json={"direction": "left"})
    assert response.status_code == 400
    assert client.get("/state").json()["snake"][0] == [5, 5]


def test_new_step_and_board(client):
    created = client.post("/new")
    assert created.status_code == 200
    assert created.json()["snake"][0] == [5, 5]

    moved = client.post("/step", json={"direction": "up"})
    assert moved.status_code == 200
    body = moved.json()
    assert body["ok"] is True
    assert body["snake"][0] == [5, 4]

    board = client.get("/")
    assert board.status_code == 200
    assert "@" in board.json()["board"]
    assert "POST /new" in board.json()["controls"]


def test_step_after_game_over_is_conflict(client):
    client.post("/new")
    game.game_over = True
    response = client.post("/step")
    assert response.status_code == 409
