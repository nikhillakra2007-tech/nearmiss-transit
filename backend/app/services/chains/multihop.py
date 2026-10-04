"""Multi-hop domino: recurring temporal sequences from pairwise occurrences.

Trails extend edge-to-edge (edge2.a == edge1.b) up to CHAIN_MAX_DEPTH edges.
Rejects: repeated near-misses, repeated routes (self-loop/cycle guard),
reversed time (impossible by construction — pairs are ordered). Groups by
route sequence; strength via strength_of; chains without any evidence excluded.
Stateless and deterministic.
"""
from __future__ import annotations
from collections import defaultdict
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.exceptions import EntityNotFoundError
from backend.app.core.logging import get_logger
from backend.app.db.models.near_miss import NearMiss
from backend.app.db.models.pattern import NearMissPattern, Pattern
from backend.app.services.chains.chain_detector import (
    _start_time, candidate_pairs, evidence_for_nm, strength_of)

log = get_logger("multihop")


def build_trails(pairs: list[dict], max_depth: int) -> list[list[dict]]:
    """DFS over occurrence edges; trails are edge lists with shared middle nodes."""
    by_source: dict[str, list[dict]] = defaultdict(list)
    for p in pairs:
        by_source[p["a"].id].append(p)
    trails: list[list[dict]] = []

    def extend(trail: list[dict], node_ids: set[str], routes: set):
        last = trail[-1]["b"]
        if len(trail) >= max_depth:
            trails.append(list(trail))
            return
        extended = False
        for nxt in by_source.get(last.id, []):
            nb = nxt["b"]
            if nb.id in node_ids or nb.route_id in routes:
                continue
            extended = True
            trail.append(nxt)
            node_ids.add(nb.id)
            routes.add(nb.route_id)
            extend(trail, node_ids, routes)
            trail.pop()
            node_ids.discard(nb.id)
            routes.discard(nb.route_id)
        if not extended and len(trail) >= 1:
            trails.append(list(trail))

    for p in pairs:
        extend([p], {p["a"].id, p["b"].id}, {p["a"].route_id, p["b"].route_id})
    # multi-hop only: single-edge trails are the pairwise view, excluded here
    return [t for t in trails if len(t) >= 2]


def detect_multihop(db: Session, agency_id: str, since=None, until=None,
                    window_minutes=None, max_depth=None,
                    member_ids: set[str] | None = None) -> list[dict]:
    max_depth = max_depth if max_depth is not None else settings.CHAIN_MAX_DEPTH
    pairs = candidate_pairs(db, agency_id, since, until, window_minutes)
    trails = build_trails(pairs, max_depth)
    groups: dict[tuple, list] = defaultdict(list)
    for trail in trails:
        if member_ids is not None and trail[0]["a"].id not in member_ids:
            continue
        seq = tuple([trail[0]["a"].route_id] + [e["b"].route_id for e in trail])
        groups[seq].append(trail)
    chains = []
    for seq, occs in groups.items():
        nodes = [occs[0][0]["a"]] + [e["b"] for e in occs[0]]
        ev: list[str] = []
        for tr in occs:
            for nm in [tr[0]["a"]] + [e["b"] for e in tr]:
                ev.extend(evidence_for_nm(db, nm.id))
        seen, eids = set(), []
        for i in ev:
            if i not in seen:
                seen.add(i)
                eids.append(i)
        if not eids:
            continue  # missing evidence: excluded, not fabricated
        gaps = [[e["gap_minutes"] for e in tr] for tr in occs]
        avg_gaps = [round(sum(col) / len(col), 1) for col in zip(*gaps)]
        chains.append({
            "route_sequence": list(seq),
            "depth": len(occs[0]),
            "strength": strength_of(len(occs)),
            "occurrences": len(occs),
            "avg_gaps": avg_gaps,
            "nodes": [{"near_miss_id": n.id, "route_id": n.route_id,
                       "type": n.near_miss_type,
                       "at": _start_time(db, n).isoformat()} for n in nodes],
            "hops": [{"from": e["a"].id, "to": e["b"].id,
                      "gap_minutes": e["gap_minutes"]} for e in occs[0]],
            "evidence_ids": eids[:20],
            "relationship": "MAY_CONTRIBUTE_TO",
        })
    chains.sort(key=lambda c: (-c["occurrences"], c["route_sequence"].__str__()))
    return chains


def pattern_multihop(db: Session, pattern_id: str, since=None, until=None,
                     window_minutes=None, max_depth=None) -> list[dict]:
    pattern = db.get(Pattern, pattern_id)
    if not pattern:
        raise EntityNotFoundError(f"pattern {pattern_id} not found")
    member_ids = {ln.near_miss_id for ln in
                  db.query(NearMissPattern).filter_by(pattern_id=pattern_id).all()}
    chains = detect_multihop(db, pattern.agency_id, since, until, window_minutes,
                             max_depth, member_ids)
    log.info(f"multihop pattern={pattern_id} n={len(chains)}")
    return chains
