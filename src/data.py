"""Data loading, caching and filtering helpers for the Sweden vs England analysis.

All data comes from StatsBomb Open Data through ``statsbombpy``. Raw downloads
are cached in ``data/raw`` as parquet files so the API is hit only once.

Time conventions used throughout the project
--------------------------------------------
* StatsBomb ``minute``/``second`` are *elapsed* match clock values. A goal at
  ``minute == 1, second == 44`` is reported on broadcasts as the 2nd minute
  (2'). ``display_minute = minute + 1``.
* ``minute`` is cumulative across periods (period 2 starts at 45, extra time at
  90 and 105, the shootout at 120). Because of stoppage time, minutes overlap
  between periods (period 1 can run to 46:37 while period 2 starts at 45:00).
  Use ``period`` together with ``minute`` when exact ordering matters.
* Pitch coordinates are StatsBomb yards (120 x 80). Every event is recorded
  from the acting team's perspective: the acting team attacks towards x = 120.
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from statsbombpy import sb

warnings.filterwarnings("ignore", message=".*credentials.*")

COMPETITION_ID = 53
SEASON_ID = 315
SWEDEN = "Sweden Women's"
ENGLAND = "England Women's"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

SHOOTOUT_PERIOD = 5
_JSON_META_KEY = b"json_columns"


# ---------------------------------------------------------------------------
# Parquet cache helpers
# ---------------------------------------------------------------------------

def _is_nested(value: object) -> bool:
    return isinstance(value, (list, dict))


def _write_parquet(df: pd.DataFrame, path: Path) -> None:
    """Write ``df`` to parquet, JSON-encoding columns that hold lists/dicts.

    StatsBomb columns such as ``location``, ``tactics`` or
    ``shot_freeze_frame`` mix nested objects with NaN, which pyarrow cannot
    store reliably. They are serialised to JSON strings and the list of
    encoded columns is stored in the parquet schema metadata.
    """
    df = df.copy()
    json_cols = [
        c for c in df.columns
        if df[c].dtype == object and df[c].map(_is_nested).any()
    ]
    for c in json_cols:
        df[c] = df[c].map(lambda v: json.dumps(v) if _is_nested(v) else None)
    # Mixed scalar types (e.g. a manager id "1001444, 5279" for co-managers among
    # integer ids) cannot be stored in one Arrow column; store those as strings.
    for c in df.columns:
        if c in json_cols or df[c].dtype != object:
            continue
        try:
            pa.array(df[c], from_pandas=True)
        except (pa.ArrowInvalid, pa.ArrowTypeError):
            df[c] = df[c].map(lambda v: None if pd.isna(v) else str(v))
    table = pa.Table.from_pandas(df, preserve_index=False)
    meta = dict(table.schema.metadata or {})
    meta[_JSON_META_KEY] = json.dumps(json_cols).encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table.replace_schema_metadata(meta), path)


def _read_parquet(path: Path) -> pd.DataFrame:
    """Read a parquet file written by :func:`_write_parquet`."""
    table = pq.read_table(path)
    meta = table.schema.metadata or {}
    json_cols = json.loads(meta.get(_JSON_META_KEY, b"[]"))
    df = table.to_pandas()
    for c in json_cols:
        df[c] = df[c].map(lambda v: json.loads(v) if isinstance(v, str) else None)
    return df


def _cached(path: Path, fetch, refresh: bool) -> pd.DataFrame:
    if path.exists() and not refresh:
        return _read_parquet(path)
    df = fetch()
    _write_parquet(df, path)
    return _read_parquet(path)


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_competitions(refresh: bool = False) -> pd.DataFrame:
    """Load (and cache) the list of competition seasons in StatsBomb Open Data."""
    return _cached(RAW_DIR / "competitions.parquet", sb.competitions, refresh)


def load_matches(
    competition_id: int = COMPETITION_ID,
    season_id: int = SEASON_ID,
    refresh: bool = False,
) -> pd.DataFrame:
    """Load (and cache) the match list for a competition season."""
    path = RAW_DIR / f"matches_{competition_id}_{season_id}.parquet"
    return _cached(
        path,
        lambda: sb.matches(competition_id=competition_id, season_id=season_id),
        refresh,
    )


def find_match_id(
    team_a: str = SWEDEN,
    team_b: str = ENGLAND,
    competition_id: int = COMPETITION_ID,
    season_id: int = SEASON_ID,
) -> int:
    """Return the StatsBomb ``match_id`` of the match between two teams.

    Args:
        team_a: StatsBomb team name, e.g. ``"Sweden Women's"``.
        team_b: StatsBomb team name, e.g. ``"England Women's"``.
        competition_id: StatsBomb competition id (53 = Women's EURO).
        season_id: StatsBomb season id (315 = 2025).

    Raises:
        ValueError: if no match or more than one match is found.
    """
    m = load_matches(competition_id, season_id)
    teams = {team_a, team_b}
    hit = m[m.apply(lambda r: {r.home_team, r.away_team} == teams, axis=1)]
    if len(hit) != 1:
        raise ValueError(f"Expected one match for {teams}, found {len(hit)}")
    return int(hit.match_id.iloc[0])


def load_events(match_id: int, refresh: bool = False) -> pd.DataFrame:
    """Load (and cache) the event data of a match, sorted by event index."""
    path = RAW_DIR / f"events_{match_id}.parquet"
    df = _cached(path, lambda: sb.events(match_id=match_id), refresh)
    return df.sort_values("index").reset_index(drop=True)


def load_lineups(match_id: int, refresh: bool = False) -> pd.DataFrame:
    """Load (and cache) both lineups of a match as one table with a ``team`` column."""
    path = RAW_DIR / f"lineups_{match_id}.parquet"

    def fetch() -> pd.DataFrame:
        lineups = sb.lineups(match_id=match_id)
        return pd.concat(
            [df.assign(team=team) for team, df in lineups.items()],
            ignore_index=True,
        )

    return _cached(path, fetch, refresh)


def load_frames_360(match_id: int, refresh: bool = False) -> pd.DataFrame:
    """Load (and cache) the StatsBomb 360 freeze frames of a match.

    One row per visible player per event. ``id`` joins to the event ``id``;
    ``teammate`` is relative to the event actor (the player performing the
    event), not to a fixed team.
    """
    path = RAW_DIR / f"frames360_{match_id}.parquet"
    return _cached(path, lambda: sb.frames(match_id=match_id), refresh)


def load_competition_events(
    competition_id: int = COMPETITION_ID,
    season_id: int = SEASON_ID,
    refresh: bool = False,
) -> pd.DataFrame:
    """Load (and cache, per match) the events of every match in a season."""
    matches = load_matches(competition_id, season_id)
    return pd.concat(
        [load_events(mid, refresh) for mid in matches.match_id.sort_values()],
        ignore_index=True,
    )


def player_display_names(lineups: pd.DataFrame) -> dict[str, str]:
    """Map StatsBomb full player names to their common name (nickname if any).

    Example: ``"Magdalena Lilly Eriksson"`` -> ``"Magdalena Eriksson"``.
    """
    names = lineups.player_nickname.fillna(lineups.player_name)
    return dict(zip(lineups.player_name, names))


# ---------------------------------------------------------------------------
# Time helpers
# ---------------------------------------------------------------------------

def clock(events: pd.DataFrame) -> pd.Series:
    """Fractional match clock in minutes (``minute + second / 60``)."""
    return events.minute + events.second / 60


def time_key(events: pd.DataFrame) -> pd.Series:
    """Monotonic ordering key ``period * 1000 + clock`` (handles stoppage overlap)."""
    return events.period * 1000 + clock(events)


# ---------------------------------------------------------------------------
# Substitutions and lineup windows
# ---------------------------------------------------------------------------

def get_substitutions(events: pd.DataFrame) -> pd.DataFrame:
    """Return all substitutions with timing, team, player off and player on.

    Columns: ``period, minute, second, display_minute, team, player_off,
    player_on, reason``. ``display_minute`` is the broadcast-style minute
    (``minute + 1``).
    """
    subs = events[events.type == "Substitution"].sort_values("index")
    return pd.DataFrame({
        "period": subs.period,
        "minute": subs.minute,
        "second": subs.second,
        "display_minute": subs.minute + 1,
        "team": subs.team,
        "player_off": subs.player,
        "player_on": subs.substitution_replacement,
        "reason": subs.substitution_outcome,
    }).reset_index(drop=True)


def get_stable_lineup_windows(
    events: pd.DataFrame,
    team: str,
    include_tactical_shifts: bool = False,
) -> pd.DataFrame:
    """Split the match (periods 1-4) into segments with an unchanged XI.

    A new segment starts at every substitution of ``team`` (and optionally at
    every Tactical Shift). Simultaneous substitutions produce one boundary
    each, which can create very short segments; these are kept so the caller
    can decide what to drop. Use :func:`filter_segment` to select the events
    of a segment.

    Returns:
        One row per segment with ``segment, start_period, start_clock,
        end_period, end_clock, duration_min, players`` (list of the players
        on the pitch) and ``n_players``. Clocks are fractional minutes.
    """
    ev = events[events.period < SHOOTOUT_PERIOD].sort_values("index")
    xi = ev[(ev.type == "Starting XI") & (ev.team == team)].tactics.iloc[0]
    on_pitch = [p["player"]["name"] for p in xi["lineup"]]

    boundary_types = ["Substitution"]
    if include_tactical_shifts:
        boundary_types.append("Tactical Shift")
    changes = ev[(ev.team == team) & ev.type.isin(boundary_types)
                 & (time_key(ev) > 1000)]  # skip kick-off markers at 0:00

    # Red cards also change the XI; StatsBomb records them on fouls / Bad Behaviour.
    card_cols = [c for c in ("foul_committed_card", "bad_behaviour_card") if c in ev]
    reds = pd.Series(False, index=ev.index)
    for c in card_cols:
        reds |= ev[c].isin(["Red Card", "Second Yellow"])
    changes = pd.concat([changes, ev[(ev.team == team) & reds]]).sort_values("index")

    last = ev.iloc[-1]
    rows: list[dict] = []
    start_period, start_clock = 1, 0.0
    for _, ch in changes.iterrows():
        ch_clock = ch.minute + ch.second / 60
        rows.append(dict(start_period=start_period, start_clock=start_clock,
                         end_period=ch.period, end_clock=ch_clock,
                         players=list(on_pitch)))
        if ch.type == "Substitution":
            on_pitch = [ch.substitution_replacement if p == ch.player else p
                        for p in on_pitch]
        elif ch.type != "Tactical Shift":  # red card
            on_pitch = [p for p in on_pitch if p != ch.player]
        start_period, start_clock = ch.period, ch_clock
    rows.append(dict(start_period=start_period, start_clock=start_clock,
                     end_period=last.period,
                     end_clock=last.minute + last.second / 60,
                     players=list(on_pitch)))

    out = pd.DataFrame(rows)
    out = out[(out.start_period * 1000 + out.start_clock)
              < (out.end_period * 1000 + out.end_clock)].reset_index(drop=True)
    out.insert(0, "segment", range(1, len(out) + 1))
    out["duration_min"] = out.apply(
        lambda s: played_minutes(ev, s.start_period, s.start_clock,
                                 s.end_period, s.end_clock),
        axis=1,
    )
    out["n_players"] = out.players.map(len)
    return out


def played_minutes(
    events: pd.DataFrame,
    start_period: int,
    start_clock: float,
    end_period: int,
    end_clock: float,
) -> float:
    """Minutes of play between two match-clock points, summed period by period.

    Stoppage time makes the clock overlap between periods (period 1 may end at
    46:37 while period 2 restarts at 45:00), so ``end - start`` is not enough.
    Period boundaries are taken from the first and last event of each period.
    """
    ev = events[events.period < SHOOTOUT_PERIOD]
    bounds = ev.assign(c=clock(ev)).groupby("period").c.agg(["min", "max"])
    total = 0.0
    for p in range(int(start_period), int(end_period) + 1):
        lo = start_clock if p == start_period else bounds.loc[p, "min"]
        hi = end_clock if p == end_period else bounds.loc[p, "max"]
        total += max(hi - lo, 0.0)
    return round(total, 2)


def filter_segment(events: pd.DataFrame, segment: pd.Series) -> pd.DataFrame:
    """Return events inside one row of :func:`get_stable_lineup_windows`."""
    key = time_key(events)
    start = segment.start_period * 1000 + segment.start_clock
    end = segment.end_period * 1000 + segment.end_clock
    return events[(key >= start) & (key < end)]


def filter_window(
    events: pd.DataFrame,
    minute_from: float,
    minute_to: float,
    team: str | None = None,
    exclude_shootout: bool = True,
) -> pd.DataFrame:
    """Select events with ``minute_from <= clock < minute_to``.

    ``clock`` is the fractional StatsBomb match clock (``minute + second/60``),
    so ``filter_window(ev, 0, 45)`` is the first 45 minutes of play *without*
    first-half stoppage time. Because the clock restarts at 45:00 in period 2,
    a window around 45-47 contains events from both periods; filter on
    ``period`` as well if that matters.

    Args:
        events: event table from :func:`load_events`.
        minute_from: inclusive lower bound (fractional minutes).
        minute_to: exclusive upper bound (fractional minutes).
        team: keep only events by this team if given.
        exclude_shootout: drop period 5 (penalty shootout) events.
    """
    c = clock(events)
    mask = (c >= minute_from) & (c < minute_to)
    if team is not None:
        mask &= events.team == team
    if exclude_shootout:
        mask &= events.period != SHOOTOUT_PERIOD
    return events[mask]


# ---------------------------------------------------------------------------
# Small geometry helpers shared by the notebooks
# ---------------------------------------------------------------------------

def split_xy(df: pd.DataFrame, col: str, prefix: str | None = None) -> pd.DataFrame:
    """Add ``{prefix}_x`` and ``{prefix}_y`` columns from a StatsBomb list column."""
    prefix = prefix or col.replace("_location", "")
    loc = df[col]
    df = df.copy()
    df[f"{prefix}_x"] = loc.map(lambda v: v[0] if isinstance(v, list) else None).astype(float)
    df[f"{prefix}_y"] = loc.map(lambda v: v[1] if isinstance(v, list) else None).astype(float)
    return df


def in_penalty_box(x: pd.Series, y: pd.Series) -> pd.Series:
    """True for attacking-penalty-box coordinates (x >= 102, 18 <= y <= 62)."""
    return (x >= 102) & (y >= 18) & (y <= 62)


def relative_path(path: Path) -> Path:
    """``path`` relative to the project root, for printing (no local directories in outputs)."""
    return Path(path).resolve().relative_to(PROJECT_ROOT)


def save_processed(df: pd.DataFrame, name: str) -> Path:
    """Save a prepared table to ``data/processed/{name}.parquet`` and return the path."""
    path = PROCESSED_DIR / f"{name}.parquet"
    _write_parquet(df, path)
    return path


def load_processed(name: str) -> pd.DataFrame:
    """Load a table saved with :func:`save_processed`."""
    return _read_parquet(PROCESSED_DIR / f"{name}.parquet")
