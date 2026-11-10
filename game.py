"""Правила змейки без HTTP. Одна партия, состояние внутри объекта Game."""

from __future__ import annotations

import random
from collections import deque
from typing import Literal

Direction = Literal["up", "down", "left", "right"]

DIRS: dict[Direction, tuple[int, int]] = {
    "up": (0, -1),
    "down": (0, 1),
    "left": (-1, 0),
    "right": (1, 0),
}

OPPOSITE: dict[Direction, Direction] = {
    "up": "down",
    "down": "up",
    "left": "right",
    "right": "left",
}


class GameError(Exception):
    """Ошибка правил, которую HTTP-слой превращает в 400 или 409."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class Game:
    def __init__(
        self,
        width: int = 10,
        height: int = 10,
        rng: random.Random | None = None,
    ) -> None:
        if width < 3 or height < 1:
            raise ValueError("board must be at least 3 cells wide and 1 cell tall")
        self.width = width
        self.height = height
        self.rng = rng or random.Random()
        self.snake: deque[tuple[int, int]] = deque()
        self.direction: Direction = "right"
        self.food: tuple[int, int] | None = None
        self.score = 0
        self.game_over = False
        self.started = False
        self.steps = 0
        self.reason: str | None = None

    def new_game(self) -> dict:
        y = min(5, self.height - 1)
        x = min(5, self.width - 1)
        if x < 2:
            x = 2
        self.snake = deque([(x, y), (x - 1, y), (x - 2, y)])
        self.direction = "right"
        self.score = 0
        self.game_over = False
        self.started = True
        self.steps = 0
        self.reason = None
        self.food = self._place_food()
        return self.snapshot()

    def step(self, direction: str | None = None) -> dict:
        if not self.started:
            raise GameError("not_started")
        if self.game_over:
            raise GameError("game_over")
        if direction is not None:
            self._turn(direction)

        dx, dy = DIRS[self.direction]
        head_x, head_y = self.snake[0]
        new_head = (head_x + dx, head_y + dy)

        if not (0 <= new_head[0] < self.width and 0 <= new_head[1] < self.height):
            self.game_over = True
            self.reason = "wall"
            return self.snapshot()

        eating = self.food is not None and new_head == self.food
        # Хвост освобождается только если змейка не ест.
        occupied = set(self.snake) if eating else set(list(self.snake)[:-1])
        if new_head in occupied:
            self.game_over = True
            self.reason = "self"
            return self.snapshot()

        self.snake.appendleft(new_head)
        if eating:
            self.score += 1
            self.food = self._place_food()
            if self.food is None:
                self.game_over = True
                self.reason = "win"
        else:
            self.snake.pop()

        self.steps += 1
        return self.snapshot()

    def snapshot(self) -> dict:
        return {
            "ok": not self.game_over,
            "snake": [list(segment) for segment in self.snake],
            "food": list(self.food) if self.food is not None else None,
            "score": self.score,
            "game_over": self.game_over,
            "started": self.started,
            "steps": self.steps,
            "direction": self.direction,
            "reason": self.reason,
            "w": self.width,
            "h": self.height,
            "board": self.render(),
        }

    def render(self) -> str:
        cells = [["." for _ in range(self.width)] for _ in range(self.height)]
        for index, (x, y) in enumerate(self.snake):
            cells[y][x] = "@" if index == 0 else "O"
        if self.food is not None:
            fx, fy = self.food
            cells[fy][fx] = "*"
        return "\n".join("".join(row) for row in cells)

    def _turn(self, direction: str) -> None:
        if direction not in DIRS or direction == OPPOSITE[self.direction]:
            raise GameError("bad_direction")
        self.direction = direction  # type: ignore[assignment]

    def _place_food(self) -> tuple[int, int] | None:
        occupied = set(self.snake)
        free = [
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if (x, y) not in occupied
        ]
        if not free:
            return None
        return self.rng.choice(free)
