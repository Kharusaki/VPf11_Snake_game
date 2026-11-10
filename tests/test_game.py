import random
from collections import deque

import pytest

from game import Game, GameError


def test_new_game_places_snake_and_food_apart():
    game = Game(rng=random.Random(1))
    snapshot = game.new_game()
    assert snapshot["snake"] == [[5, 5], [4, 5], [3, 5]]
    assert snapshot["food"] not in snapshot["snake"]
    assert snapshot["score"] == 0
    assert snapshot["started"] is True
    assert "@" in snapshot["board"]
    assert "*" in snapshot["board"]


def test_step_moves_head_right():
    game = Game(rng=random.Random(1))
    game.new_game()
    snapshot = game.step()
    assert snapshot["snake"][0] == [6, 5]
    assert snapshot["steps"] == 1
    assert snapshot["ok"] is True


def test_wall_ends_the_game_without_moving():
    game = Game(4, 4, random.Random(0))
    game.started = True
    game.direction = "left"
    game.snake = deque([(0, 0), (1, 0), (2, 0)])
    game.food = (3, 3)
    snapshot = game.step()
    assert snapshot["reason"] == "wall"
    assert snapshot["game_over"] is True
    assert snapshot["snake"][0] == [0, 0]
    assert snapshot["steps"] == 0


def test_reverse_is_rejected_and_does_not_move():
    game = Game(rng=random.Random(1))
    game.new_game()
    before = game.snapshot()["snake"]
    with pytest.raises(GameError) as caught:
        game.step("left")
    assert caught.value.code == "bad_direction"
    assert game.snapshot()["snake"] == before


def test_unknown_direction_is_rejected():
    game = Game(rng=random.Random(1))
    game.new_game()
    with pytest.raises(GameError) as caught:
        game.step("north")
    assert caught.value.code == "bad_direction"


def test_moving_into_vacating_tail_is_allowed():
    game = Game(4, 4, random.Random(0))
    game.started = True
    game.direction = "left"
    game.snake = deque([(1, 0), (1, 1), (0, 0)])
    game.food = (3, 3)
    snapshot = game.step()
    assert snapshot["game_over"] is False
    assert snapshot["snake"][0] == [0, 0]
    assert snapshot["reason"] is None


def test_moving_into_tail_while_eating_is_death():
    game = Game(4, 4, random.Random(0))
    game.started = True
    game.direction = "left"
    game.snake = deque([(1, 0), (1, 1), (0, 0)])
    game.food = (0, 0)
    snapshot = game.step()
    assert snapshot["reason"] == "self"
    assert snapshot["snake"][0] == [1, 0]


def test_hitting_the_body_is_death():
    game = Game(4, 4, random.Random(0))
    game.started = True
    game.direction = "down"
    game.snake = deque([(1, 0), (2, 0), (2, 1), (1, 1), (0, 1)])
    game.food = (3, 3)
    snapshot = game.step()
    assert snapshot["reason"] == "self"


def test_filling_the_board_wins_instead_of_hanging():
    game = Game(4, 1, random.Random(0))
    game.started = True
    game.direction = "right"
    game.snake = deque([(2, 0), (1, 0), (0, 0)])
    game.food = (3, 0)
    snapshot = game.step()
    assert snapshot["reason"] == "win"
    assert snapshot["food"] is None
    assert len(snapshot["snake"]) == 4
    assert snapshot["score"] == 1


def test_step_before_start_and_after_game_over():
    game = Game()
    with pytest.raises(GameError) as caught:
        game.step()
    assert caught.value.code == "not_started"

    game.started = True
    game.game_over = True
    game.snake = deque([(1, 0), (2, 0), (3, 0)])
    with pytest.raises(GameError) as caught:
        game.step()
    assert caught.value.code == "game_over"
