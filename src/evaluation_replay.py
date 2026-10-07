import json
from pathlib import Path


REPLAY_FILE = Path("data/evaluation_replay.json")


def load_replay() -> dict:
    if not REPLAY_FILE.exists():
        return {}

    with open(REPLAY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_replay(replay: dict):
    REPLAY_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(REPLAY_FILE, "w", encoding="utf-8") as f:
        json.dump(replay, f, indent=2)


def get_replayed_sql(question: str):
    replay = load_replay()
    entry = replay.get(question)

    if entry:
        return entry.get("sql")

    return None


def save_replayed_sql(question: str, sql: str):
    replay = load_replay()

    replay[question] = {
        "sql": sql,
    }

    save_replay(replay)