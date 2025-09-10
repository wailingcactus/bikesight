import os
import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Lyft Bike App", page_icon="🚲", layout="wide")
st.title("🚲 Lyft Bike App — Starter")

st.markdown('''
This starter shows two things:
1) Load and analyze a local CSV of historical trips.
2) (Optional) Pull live station status from a GBFS feed if you provide an index URL in `secrets`.
''')

@st.cache_data
def load_csv(path: str):
    try:
        return pd.read_csv(path, low_memory=False)
    except Exception as e:
        st.info(f"Could not load CSV at `{path}`. Error: {e}")
        return None

@st.cache_data(ttl=30)
def fetch_json(url: str) -> dict:
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.json()

def find_feed_url(gbfs_index: dict, feed_name: str):
    try:
        languages = gbfs_index["data"]
        lang_key = next(iter(languages))
        feeds = languages[lang_key]["feeds"]
        for f in feeds:
            if f.get("name") == feed_name:
                return f.get("url")
    except Exception:
        pass
    return None

# ---------- Historical CSV section ----------
st.header("Part 1 — Historical trips (CSV)")
csv_path = os.path.join("data", "baywheels-tripdata.csv")
df = load_csv(csv_path)

if df is not None:
    st.write("Preview:", df.head())
    possible_start_cols = ["start_station_name", "start_station", "start_station_id"]
    possible_end_cols = ["end_station_name", "end_station", "end_station_id"]
    start_col = next((c for c in possible_start_cols if c in df.columns), None)
    end_col = next((c for c in possible_end_cols if c in df.columns), None)
    if start_col and end_col:
        trips = df[[start_col, end_col]].dropna()
        trips = trips[trips[start_col] != trips[end_col]]
        def route_key(row):
            a, b = str(row[start_col]), str(row[end_col])
            return " ↔ ".join(sorted([a, b]))
        trips["route"] = trips.apply(route_key, axis=1)
        top_routes = trips["route"].value_counts().head(10).rename_axis("route").reset_index(name="trips")
        st.subheader("Top routes (bidirectional)")
        st.dataframe(top_routes, use_container_width=True)
    else:
        st.warning("Couldn't find station columns.")
else:
    st.info("Add a CSV to `./data/baywheels-tripdata.csv`.")

# ---------- Live GBFS section ----------
st.header("Part 2 — Live GBFS (optional)")
index_url = st.secrets.get("GBFS_INDEX_URL")
if not index_url:
    st.info("No `GBFS_INDEX_URL` set in secrets.")
else:
    try:
        gbfs_index = fetch_json(index_url)
        station_info_url = find_feed_url(gbfs_index, "station_information")
        station_status_url = find_feed_url(gbfs_index, "station_status")
        if not station_info_url or not station_status_url:
            st.error("Could not locate GBFS feeds.")
        else:
            info = fetch_json(station_info_url)
            status = fetch_json(station_status_url)
            info_df = pd.DataFrame(info["data"]["stations"])
            status_df = pd.DataFrame(status["data"]["stations"])
            merged = info_df.merge(status_df, on="station_id", suffixes=("_info", "_status"))
            cols = [c for c in ["name","lat","lon","num_bikes_available","num_docks_available","is_installed","is_renting","is_returning"] if c in merged.columns]
            st.subheader("Live station snapshot")
            sort_col = "num_bikes_available" if "num_bikes_available" in cols else cols[0]
            st.dataframe(merged[cols].sort_values(by=sort_col, ascending=False).head(20), use_container_width=True)
    except Exception as e:
        st.error(f"Failed to fetch GBFS data: {e}")
