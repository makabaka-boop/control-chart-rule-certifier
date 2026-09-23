"""FastAPI service: validates inputs (422 on unknown fields / out of range)
and returns the control-chart rule evaluation."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, StrictInt

from .rules import evaluate

app = FastAPI(title="SPC 控制图核验台", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChartRequest(BaseModel):
    model_config = {"extra": "forbid"}

    target: StrictInt
    sigma: StrictInt = Field(gt=0)
    readings: list[StrictInt] = Field(min_length=2, max_length=200)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/evaluate")
def evaluate_chart(req: ChartRequest) -> dict:
    return evaluate(req.readings, req.target, req.sigma)
