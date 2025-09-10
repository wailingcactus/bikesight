import os
import io
import sqlite3
from urllib.parse import urljoin
from zipfile import ZipFile

import pandas as pd
import requests
from bs4 import BeautifulSoup


def load_trips_from_db(db_path: str, s3_index_url: str) -> pd.DataFrame:
    """Load trip data from a SQLite database or from S3 if the database is missing.

    Parameters
    ----------
    db_path: str
        Location of the SQLite database file.
    s3_index_url: str
        URL to the S3 index HTML listing trip data zip files.

    Returns
    -------
    pandas.DataFrame
        Combined trip records.
    """
    if os.path.exists(db_path):
        with sqlite3.connect(db_path) as conn:
            return pd.read_sql("SELECT * FROM trips", conn)

    resp = requests.get(s3_index_url, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    links = [urljoin(s3_index_url, a["href"]) for a in soup.find_all("a", href=True) if a["href"].endswith(".zip")]

    frames = []
    for link in links:
        with requests.get(link, stream=True) as r:
            r.raise_for_status()
            buffer = io.BytesIO()
            for chunk in r.iter_content(chunk_size=8192):
                buffer.write(chunk)
            buffer.seek(0)
            with ZipFile(buffer) as zf:
                for name in zf.namelist():
                    if name.endswith(".csv"):
                        with zf.open(name) as f:
                            frames.append(pd.read_csv(f))

    df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        df.to_sql("trips", conn, if_exists="replace", index=False)
    return df
