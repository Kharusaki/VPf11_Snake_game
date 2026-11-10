"""HTTP-сервис змейки. Одна общая партия, ход под замком."""

from __future__ import annotations

import logging
import threading

from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from game import Direction, Game, GameError

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("snake")

game = Game()
lock = threading.Lock()

app = FastAPI(
    title="Snake Service",
    version="1.0.0",
    description="Пошаговая змейка. Одна партия на процесс.",
)


class MoveRequest(BaseModel):
    direction: Direction | None = None


@app.exception_handler(RequestValidationError)
def validation_error(_: Request, __: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"detail": "direction must be up, down, left or right"},
    )


def _http_error(exc: GameError) -> HTTPException:
    if exc.code == "bad_direction":
        return HTTPException(
            status_code=400,
            detail="direction must be up, down, left or right and must not reverse the snake",
        )
    if exc.code == "not_started":
        return HTTPException(status_code=409, detail="game not started")
    if exc.code == "game_over":
        return HTTPException(status_code=409, detail="game over")
    return HTTPException(status_code=400, detail=exc.code)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/new")
def new_game() -> dict:
    with lock:
        snapshot = game.new_game()
        logger.info("new game started")
        return snapshot


@app.post("/step")
def step(req: MoveRequest | None = Body(default=None)) -> dict:
    direction = None if req is None else req.direction
    with lock:
        try:
            snapshot = game.step(direction)
        except GameError as exc:
            raise _http_error(exc) from exc
        if snapshot["reason"] == "wall":
            logger.info("hit wall")
        elif snapshot["reason"] == "self":
            logger.info("bit itself")
        elif snapshot["reason"] == "win":
            logger.info("board cleared")
        return snapshot


@app.get("/state")
def state() -> dict:
    with lock:
        return game.snapshot()


@app.get("/")
def root() -> dict:
    with lock:
        snapshot = game.snapshot()
    return {
        "board": snapshot["board"],
        "score": snapshot["score"],
        "game_over": snapshot["game_over"],
        "controls": "POST /new, then POST /step {direction: up|down|left|right}",
    }
