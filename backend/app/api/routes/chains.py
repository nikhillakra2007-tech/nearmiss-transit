"""Chain endpoints: computed relationship views (no new tables)."""
from __future__ import annotations
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.app.api.deps import get_db
from backend.app.core.exceptions import NearMissError
from backend.app.services.chains.chain_agent import investigate_chain
from backend.app.services.chains.chain_detector import pattern_chains
from backend.app.services.chains.multihop import pattern_multihop

router = APIRouter()


def _parse(dt: str | None):
    if not dt:
        return None
    try:
        return datetime.fromisoformat(dt)
    except ValueError:
        raise HTTPException(422, f"bad datetime: {dt}")


@router.get("/patterns/{pattern_id}/chains")
def get_chains(pattern_id: str, since: str | None = None, until: str | None = None,
               window_minutes: int | None = None, db: Session = Depends(get_db)):
    try:
        chains, _ = pattern_chains(db, pattern_id, _parse(since), _parse(until), window_minutes)
    except NearMissError as e:
        raise HTTPException(e.status_code, e.code)
    return {"pattern_id": pattern_id, "chains": chains,
            "disclaimer": "Temporal association, not causal proof."}


class ChainInvestigateIn(BaseModel):
    chain_key: str
    since: str | None = None
    until: str | None = None
    window_minutes: int | None = None


@router.get("/patterns/{pattern_id}/multihop")
def get_multihop(pattern_id: str, since: str | None = None, until: str | None = None,
                 window_minutes: int | None = None, max_depth: int | None = None,
                 db: Session = Depends(get_db)):
    if max_depth is not None and not (1 <= max_depth <= 5):
        raise HTTPException(422, "max_depth must be within 1..5")
    try:
        chains = pattern_multihop(db, pattern_id, _parse(since), _parse(until),
                                  window_minutes, max_depth)
    except NearMissError as e:
        raise HTTPException(e.status_code, e.code)
    return {"pattern_id": pattern_id, "chains": chains,
            "disclaimer": "Shows recurring temporal sequences, not proven causation."}


@router.post("/patterns/{pattern_id}/chains/investigate")
def investigate_chains(pattern_id: str, body: ChainInvestigateIn, db: Session = Depends(get_db)):
    try:
        return investigate_chain(db, pattern_id, body.chain_key, _parse(body.since),
                                 _parse(body.until), body.window_minutes)
    except NearMissError as e:
        raise HTTPException(e.status_code, e.code)
