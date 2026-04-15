import argparse
import hashlib
import json
import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).with_name("users.db")
TARGET_SITE_PATTERNS = [
    "%uitu.edu.pk%",
    "%geo.tv%",
    "%geonews%",
    "%aljazeera.com%",
]
USER_SCOPED_TABLES = [
    "cloned_sites",
    "site_specs",
    "dynamic_models",
    "dynamic_records",
    "media_assets",
]


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def ensure_demo_user(conn: sqlite3.Connection, username: str, password: str) -> sqlite3.Row:
    existing = conn.execute(
        "SELECT id, username FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    password_hash = hash_password(password)
    if existing:
        conn.execute(
            "UPDATE users SET password = ? WHERE id = ?",
            (password_hash, existing["id"]),
        )
        return existing

    conn.execute(
        "INSERT INTO users (username, password, created_at) VALUES (?, ?, datetime('now'))",
        (username, password_hash),
    )
    user_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
    return conn.execute(
        "SELECT id, username FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()


def discover_target_sites(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    clauses = " OR ".join(["LOWER(url) LIKE ?"] * len(TARGET_SITE_PATTERNS))
    query = f"""
        SELECT id, user_id, url, cloned_at
        FROM cloned_sites
        WHERE {clauses}
        ORDER BY id DESC
    """
    return conn.execute(query, [pattern.lower() for pattern in TARGET_SITE_PATTERNS]).fetchall()


def load_selected_sites(conn: sqlite3.Connection, explicit_ids: list[int] | None) -> list[sqlite3.Row]:
    if explicit_ids:
        placeholders = ",".join(["?"] * len(explicit_ids))
        query = f"""
            SELECT id, user_id, url, cloned_at
            FROM cloned_sites
            WHERE id IN ({placeholders})
            ORDER BY id DESC
        """
        return conn.execute(query, explicit_ids).fetchall()
    return discover_target_sites(conn)


def reassign_sites(conn: sqlite3.Connection, site_ids: list[int], demo_user_id: int) -> dict[str, int]:
    if not site_ids:
        return {table: 0 for table in USER_SCOPED_TABLES}

    placeholders = ",".join(["?"] * len(site_ids))
    summary: dict[str, int] = {}
    for table in USER_SCOPED_TABLES:
        sql = f"UPDATE {table} SET user_id = ? WHERE site_id IN ({placeholders})" if table != "cloned_sites" else f"UPDATE {table} SET user_id = ? WHERE id IN ({placeholders})"
        cursor = conn.execute(sql, [demo_user_id, *site_ids])
        summary[table] = cursor.rowcount
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare a repeatable local jury demo user.")
    parser.add_argument("--username", default="jurydemo", help="Demo username to create or reset.")
    parser.add_argument("--password", default="jurydemo123", help="Demo password to create or reset.")
    parser.add_argument("--site-id", type=int, action="append", dest="site_ids", help="Specific site id(s) to assign to the demo user.")
    args = parser.parse_args()

    if not DB_PATH.exists():
        raise SystemExit(f"Database not found: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    demo_user = ensure_demo_user(conn, args.username, args.password)
    selected_sites = load_selected_sites(conn, args.site_ids)
    site_ids = [row["id"] for row in selected_sites]
    reassignment_summary = reassign_sites(conn, site_ids, demo_user["id"])
    conn.commit()
    conn.close()

    payload = {
        "demoUser": {
            "id": demo_user["id"],
            "username": args.username,
            "password": args.password,
        },
        "assignedSiteIds": site_ids,
        "assignedSites": [
            {
                "id": row["id"],
                "url": row["url"],
                "cloned_at": row["cloned_at"],
            }
            for row in selected_sites
        ],
        "updatedRows": reassignment_summary,
        "note": "If Geo News or Al Jazeera are cloned later, rerun this script to assign them to the same demo user.",
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
