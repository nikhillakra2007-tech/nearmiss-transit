"""Seed DEMO/REPLAY data (clearly labelled, never presented as live).
Includes multi-corridor transit network:
- Route 42 (Forest Hills - Dudley) -> Route 17 -> Route 8 lagged replay sequence (4 windows)
- Route 1 (Mass Ave Bus: Harvard - Nubian) high-frequency bridge corridor
- Route 66 (Harvard - Allston - Brookline) urban bottleneck corridor
- Red Line (Heavy Rail: Alewife - Braintree/Ashmont) dwell spike & recovery
- Green Line E (Light Rail: Heath St - Medford/Tufts) surface bottleneck
- Route 39 (Forest Hills - Back Bay via Huntington Ave)
- Orange Line (Subway: Oak Grove - Forest Hills)
Usage: python scripts/seed_demo.py
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime, timedelta, timezone
from backend.app.db.session import SessionLocal
from backend.app.db.base import Base
from backend.app.db.session import engine
from backend.app.db import models  # noqa
from backend.app.db.models.agency import Agency
from backend.app.db.models.route import Route
from backend.app.db.models.vehicle import Vehicle
from backend.app.db.models.transit_event import TransitEvent


def _route(db, agency, ext, short_name=None, long_name=None):
    r = db.query(Route).filter_by(agency_id=agency.id, external_route_id=ext).first()
    if not r:
        r = Route(agency_id=agency.id, external_route_id=ext, short_name=short_name or ext, long_name=long_name)
        db.add(r)
        db.commit()
        db.refresh(r)
    else:
        changed = False
        if short_name and r.short_name != short_name:
            r.short_name = short_name
            changed = True
        if long_name and r.long_name != long_name:
            r.long_name = long_name
            changed = True
        if changed:
            db.commit()
            db.refresh(r)
    return r


def _vehicle(db, agency, ext):
    v = db.query(Vehicle).filter_by(agency_id=agency.id, external_vehicle_id=ext).first()
    if not v:
        v = Vehicle(agency_id=agency.id, external_vehicle_id=ext)
        db.add(v)
        db.commit()
        db.refresh(v)
    return v


def _add_series(db, agency, route, veh, at, delays, tag):
    for i, d in enumerate(delays):
        sid = f"demo-{tag}-{i}"
        if db.query(TransitEvent).filter_by(agency_id=agency.id, source_event_id=sid).first():
            continue  # idempotent re-seed
        db.add(TransitEvent(agency_id=agency.id, route_id=route.id, vehicle_id=veh.id,
                            event_type="TRIP_UPDATE", observed_at=at + timedelta(minutes=i * 5),
                            delay_seconds=d, status="OBSERVED", source="DEMO/REPLAY",
                            source_event_id=sid, raw_payload={"demo": True},
                            normalized_payload={"delay_seconds": d}))
    db.commit()


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    agency = db.query(Agency).filter_by(external_id="demo-agency").first()
    if not agency:
        agency = Agency(external_id="demo-agency", name="Demo Transit Agency (REPLAY)")
        db.add(agency)
        db.commit()
        db.refresh(agency)

    # Multi-modal network routes
    r42 = _route(db, agency, "42", "42", "Forest Hills - Dudley via Washington St")
    r17 = _route(db, agency, "17", "17", "Fields Corner - Andrew via Uphams Corner")
    r8 = _route(db, agency, "8", "8", "Harbor Point/UMass - Kenmore via BUMC")
    r1 = _route(db, agency, "1", "1", "Harvard Square - Nubian Station via Mass Ave")
    r66 = _route(db, agency, "66", "66", "Harvard Square - Nubian via Allston & Brookline")
    r_red = _route(db, agency, "Red", "Red Line", "Alewife - Braintree/Ashmont Heavy Rail Subway")
    r_green = _route(db, agency, "Green-E", "Green Line E", "Heath Street - Medford/Tufts Light Rail")
    r39 = _route(db, agency, "39", "39", "Forest Hills - Back Bay via Huntington Ave")
    r_orange = _route(db, agency, "Orange", "Orange Line", "Oak Grove - Forest Hills Subway")

    base = datetime.now(timezone.utc) - timedelta(hours=2)

    # 1. Route 42 near-miss episodes with natural operational variation
    r42_initial = [
        [310, 720, 1140, 920, 510, 205],  # Peak 19.0 min, final 3.4 min
        [280, 660, 1050, 860, 470, 185],  # Peak 17.5 min, final 3.1 min
        [340, 760, 1200, 970, 550, 225],  # Peak 20.0 min, final 3.8 min
    ]
    for idx, v in enumerate(("V1", "V2", "V3")):
        _add_series(db, agency, r42, _vehicle(db, agency, v),
                    base - timedelta(days=idx + 1) + timedelta(minutes=idx * 3),
                    r42_initial[idx], v)

    # 2. Domino replay: 4 windows with natural variations per occurrence
    # Route 17 spike lags Route 42 spike by ~12 min, Route 8 lags by ~24 min
    r42_windows = [
        [300, 710, 1120, 905, 505, 200],  # Peak 18.7 min
        [285, 685, 1075, 875, 495, 190],  # Peak 17.9 min
        [330, 750, 1180, 960, 540, 220],  # Peak 19.7 min
        [295, 695, 1090, 890, 500, 195],  # Peak 18.2 min
    ]
    r17_windows = [
        [250, 655, 1010, 810, 455, 180],  # Peak 16.8 min
        [220, 610, 950, 760, 430, 160],   # Peak 15.8 min
        [280, 700, 1080, 860, 490, 200],  # Peak 18.0 min
        [240, 640, 980, 785, 445, 170],   # Peak 16.3 min
    ]
    r8_windows = [
        [105, 315, 925, 715, 415, 155],   # Peak 15.4 min, final 2.6 min
        [85, 270, 840, 640, 370, 130],    # Peak 14.0 min, final 2.2 min
        [130, 360, 1010, 795, 460, 180],  # Peak 16.8 min, final 3.0 min
        [95, 295, 890, 685, 400, 145],    # Peak 14.8 min, final 2.4 min
    ]
    for k in range(4):
        wb = base - timedelta(days=k + 1) + timedelta(minutes=k * 2)
        _add_series(db, agency, r42, _vehicle(db, agency, f"C42-{k}"), wb, r42_windows[k], f"C42-{k}")
        _add_series(db, agency, r17, _vehicle(db, agency, f"C17-{k}"), wb + timedelta(minutes=12), r17_windows[k], f"C17-{k}")
        _add_series(db, agency, r8, _vehicle(db, agency, f"C8-{k}"), wb + timedelta(minutes=24), r8_windows[k], f"C8-{k}")

    # 3. Route 1 (Mass Ave Bus) - Recurring bridge bottleneck delay spikes
    r1_series = [
        [180, 240, 1020, 810, 440, 160],  # Peak 17.0 min
        [220, 280, 1160, 875, 485, 195],  # Peak 19.3 min
        [165, 230, 975, 770, 420, 150],   # Peak 16.3 min
        [240, 290, 1210, 910, 510, 210],  # Peak 20.2 min
    ]
    for k, veh_name in enumerate(("R1-101", "R1-102", "R1-103", "R1-104")):
        _add_series(db, agency, r1, _vehicle(db, agency, veh_name),
                    base - timedelta(days=k) + timedelta(minutes=k * 3),
                    r1_series[k], veh_name)

    # 4. Route 66 (Harvard-Allston-Brookline) - Recurring urban choke point near Coolidge Corner
    r66_series = [
        [200, 250, 1050, 830, 455, 175],  # Peak 17.5 min
        [240, 290, 1195, 895, 510, 205],  # Peak 19.9 min
        [185, 235, 990, 800, 435, 160],   # Peak 16.5 min
        [250, 300, 1230, 920, 525, 215],  # Peak 20.5 min
    ]
    for k, veh_name in enumerate(("R66-201", "R66-202", "R66-203", "R66-204")):
        _add_series(db, agency, r66, _vehicle(db, agency, veh_name),
                    base - timedelta(days=k) + timedelta(minutes=k * 3),
                    r66_series[k], veh_name)

    # 5. Red Line (Heavy Rail Subway) - Dwell time surges at Downtown Crossing & Park St
    rl_series = [
        [160, 210, 990, 780, 410, 135],   # Peak 16.5 min
        [210, 260, 1140, 860, 470, 170],  # Peak 19.0 min
        [150, 200, 930, 740, 390, 120],   # Peak 15.5 min
        [225, 275, 1180, 890, 490, 180],  # Peak 19.7 min
    ]
    for k, veh_name in enumerate(("RL-Train-1", "RL-Train-2", "RL-Train-3", "RL-Train-4")):
        _add_series(db, agency, r_red, _vehicle(db, agency, veh_name),
                    base - timedelta(days=k) + timedelta(minutes=k * 3),
                    rl_series[k], veh_name)

    # 6. Green Line E (Light Rail) - Mixed traffic surface running bottleneck on Huntington Ave
    gle_series = [
        [190, 240, 1020, 800, 430, 155],  # Peak 17.0 min
        [230, 280, 1150, 865, 475, 185],  # Peak 19.2 min
        [175, 225, 970, 775, 415, 145],   # Peak 16.2 min
        [240, 290, 1190, 895, 495, 195],  # Peak 19.8 min
    ]
    for k, veh_name in enumerate(("GLE-301", "GLE-302", "GLE-303", "GLE-304")):
        _add_series(db, agency, r_green, _vehicle(db, agency, veh_name),
                    base - timedelta(days=k) + timedelta(minutes=k * 3),
                    gle_series[k], veh_name)

    # 7. Route 39 (Forest Hills - Back Bay) - Articulated bus corridor
    r39_series = [
        [170, 220, 990, 780, 410, 145],  # Peak 16.5 min
        [205, 260, 1110, 840, 460, 175],  # Peak 18.5 min
        [155, 210, 930, 750, 390, 130],   # Peak 15.5 min
        [220, 270, 1170, 880, 480, 190],  # Peak 19.5 min
    ]
    for k, veh_name in enumerate(("R39-401", "R39-402", "R39-403", "R39-404")):
        _add_series(db, agency, r39, _vehicle(db, agency, veh_name),
                    base - timedelta(days=k) + timedelta(minutes=k * 3),
                    r39_series[k], veh_name)

    # 8. Emerging tail (REPLAY): recent sub-threshold rising delays on route 42
    tail_at = datetime.now(timezone.utc) - timedelta(minutes=45)
    tail_veh = _vehicle(db, agency, "TAIL-1")
    _add_series(db, agency, r42, tail_veh, tail_at,
                [400, 430, 460, 480, 500, 520, 540, 560, 580], "TAIL-1")

    # 9. Diverse normal background operations across all corridors for honest baselines & live matrix
    bg_veh = _vehicle(db, agency, "BG-1")
    for j, d in enumerate([60, 90, 120, 80, 110, 70, 100, 130, 90, 105, 75, 140,
                           65, 95, 125, 85, 115, 140, 70, 100, 120, 80, 110, 90]):
        _add_series(db, agency, r42, bg_veh,
                    datetime.now(timezone.utc) - timedelta(hours=72 - j * 2.5),
                    [d], f"BG-1-{j}")

    # Background for Route 1, Route 66, Red Line, Green Line E, Route 39, Orange Line
    bg_configs = [
        (r1, "BG-R1", [70, 95, 110, 85, 105, 90, 120, 80, 100, 75, 115, 95]),
        (r66, "BG-R66", [80, 110, 130, 90, 115, 100, 125, 85, 105, 90, 120, 100]),
        (r_red, "BG-RL", [40, 60, 80, 50, 70, 65, 85, 55, 75, 60, 90, 70]),
        (r_green, "BG-GLE", [65, 90, 115, 80, 100, 85, 110, 75, 95, 80, 105, 90]),
        (r39, "BG-R39", [60, 85, 105, 75, 95, 80, 100, 70, 90, 75, 105, 85]),
        (r_orange, "BG-OL", [45, 70, 90, 55, 75, 60, 80, 50, 70, 65, 85, 60]),
    ]
    for r_target, v_tag, delays_list in bg_configs:
        v_obj = _vehicle(db, agency, v_tag)
        for j, d in enumerate(delays_list):
            _add_series(db, agency, r_target, v_obj,
                        datetime.now(timezone.utc) - timedelta(hours=48 - j * 3.5),
                        [d], f"{v_tag}-{j}")

    print("demo seed complete (DEMO/REPLAY mode, multi-corridor transit network seeded)")
