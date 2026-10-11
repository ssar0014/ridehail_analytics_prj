import threading
import time
from datetime import datetime, timezone

import pydeck as pdk
import streamlit as st

from generators.real_time.real_time_generator import RealTimeGenerator
from models.fare_model import Fare
from models.ride_event_model import RideEvent

_SF_LAT, _SF_LON = 37.76, -122.44


def _stream(gen: RealTimeGenerator, rides: dict, stats: dict, lock: threading.Lock) -> None:
    for payload in gen.stream():
        if isinstance(payload, RideEvent):
            wait = (payload.occurred_at - datetime.now(timezone.utc)).total_seconds()
            if wait > 0:
                time.sleep(wait)

            rid = str(payload.ride_id)
            with lock:
                if rid not in rides:
                    rides[rid] = {
                        "path":    [],
                        "lat":     payload.latitude,
                        "lon":     payload.longitude,
                        "done":    False,
                        "done_at": None,
                    }
                r = rides[rid]
                r["lat"] = payload.latitude
                r["lon"] = payload.longitude
                r["path"].append([payload.longitude, payload.latitude])
                stats["total_events"] += 1

        elif isinstance(payload, Fare):
            rid = str(payload.ride_id)
            with lock:
                if rid in rides:
                    rides[rid]["done"]    = True
                    rides[rid]["done_at"] = datetime.now(timezone.utc)
                stats["completed_rides"] += 1

        # Prune rides completed more than 30 s ago
        now = datetime.now(timezone.utc)
        with lock:
            stale = [
                k for k, v in rides.items()
                if v["done"] and v["done_at"] and (now - v["done_at"]).total_seconds() > 30
            ]
            for k in stale:
                del rides[k]


# ── Streamlit app ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="RideHail Live Map", layout="wide")
st.title("RideHail Live Map")

# Initialise shared state once per session — persists across reruns
if "rides" not in st.session_state:
    st.session_state.rides = {}
    st.session_state.stats = {"total_events": 0, "completed_rides": 0}
    st.session_state.lock  = threading.Lock()

    gen = RealTimeGenerator(
        n_concurrent=5,
        n_drivers=20,
        n_customers=50,
        location_update_interval_seconds=2,
    )
    threading.Thread(
        target=_stream,
        args=(gen, st.session_state.rides, st.session_state.stats, st.session_state.lock),
        daemon=True,
    ).start()

# Read a snapshot of the shared state
with st.session_state.lock:
    rides_snapshot = {k: dict(v) for k, v in st.session_state.rides.items()}
    stats_snapshot = dict(st.session_state.stats)

active_rides = [r for r in rides_snapshot.values() if not r["done"]]

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Live Stats")
    st.metric("Active Rides",    len(active_rides))
    st.metric("Completed Rides", stats_snapshot["completed_rides"])
    st.metric("Total Events",    stats_snapshot["total_events"])
    st.caption(f"Refreshed at {datetime.now().strftime('%H:%M:%S')}")

# ── PyDeck layers ─────────────────────────────────────────────────────────────
scatter_data = [{"lon": r["lon"], "lat": r["lat"]} for r in active_rides]

path_data = [{"path": r["path"]} for r in active_rides if len(r["path"]) > 1]

scatter_layer = pdk.Layer(
    "ScatterplotLayer",
    data=scatter_data,
    get_position="[lon, lat]",
    get_color=[0, 220, 120, 230],
    get_radius=100,
    radius_min_pixels=6,
    pickable=True,
)

path_layer = pdk.Layer(
    "PathLayer",
    data=path_data,
    get_path="path",
    get_color=[30, 160, 255, 180],
    get_width=5,
    width_min_pixels=2,
)

view = pdk.ViewState(latitude=_SF_LAT, longitude=_SF_LON, zoom=12, pitch=0)

st.pydeck_chart(pdk.Deck(
    layers=[path_layer, scatter_layer],
    initial_view_state=view,
    map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
))

time.sleep(2)
st.rerun()
