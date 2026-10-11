"""
Manage web-app login accounts (app_users).

Usage:
    # Create demo admin / driver / customer accounts (password: ridehail)
    uv run python -m api.users demo

    # Create a specific account
    uv run python -m api.users create --email ops@ridehail.dev --role admin
    uv run python -m api.users create --email d@x.com --role driver --driver-id <uuid>
"""

import argparse
import getpass
from uuid import UUID

import psycopg

from api.security import hash_password
from db.connection import get_conn
from enums.user_role import UserRole

DEMO_PASSWORD = "ridehail"


def create_user(
    conn: psycopg.Connection,
    email: str,
    password: str,
    role: UserRole,
    driver_id: UUID | None = None,
    customer_id: UUID | None = None,
) -> bool:
    """Insert an account; returns False if the email (or linked entity) already has one."""
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO app_users (email, password_hash, role, driver_id, customer_id) "
            "VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
            (email.strip().lower(), hash_password(password), role, driver_id, customer_id),
        )
        return cur.rowcount == 1


def _first_id(conn: psycopg.Connection, table: str, column: str) -> UUID | None:
    # The oldest row, so `demo` links to the same entity on every run
    with conn.cursor() as cur:
        cur.execute(f"SELECT {column} FROM {table} ORDER BY created_at, {column} LIMIT 1")
        row = cur.fetchone()
        return row[0] if row else None


def seed_demo() -> None:
    with get_conn() as conn:
        accounts = [("admin@ridehail.dev", UserRole.ADMIN, {})]

        if driver_id := _first_id(conn, "drivers", "driver_id"):
            accounts.append(("driver@ridehail.dev", UserRole.DRIVER, {"driver_id": driver_id}))
        else:
            print("  skipped  driver@ridehail.dev (no drivers loaded — run db/batch_loader.py)")

        if customer_id := _first_id(conn, "customers", "customer_id"):
            accounts.append(("customer@ridehail.dev", UserRole.CUSTOMER, {"customer_id": customer_id}))
        else:
            print("  skipped  customer@ridehail.dev (no customers loaded — run db/batch_loader.py)")

        for email, role, links in accounts:
            created = create_user(conn, email, DEMO_PASSWORD, role, **links)
            print(f"  {'created' if created else 'exists '}  {email} ({role})")
        conn.commit()
    print(f"Demo password: {DEMO_PASSWORD}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("demo", help="create demo admin/driver/customer accounts")

    create = sub.add_parser("create", help="create a single account")
    create.add_argument("--email", required=True)
    create.add_argument("--role", required=True, choices=[r.value for r in UserRole])
    create.add_argument("--driver-id", type=UUID)
    create.add_argument("--customer-id", type=UUID)

    args = parser.parse_args()
    if args.command == "demo":
        seed_demo()
        return

    role = UserRole(args.role)
    if (role == UserRole.DRIVER) != (args.driver_id is not None):
        parser.error("--driver-id is required for, and only valid with, --role driver")
    if (role == UserRole.CUSTOMER) != (args.customer_id is not None):
        parser.error("--customer-id is required for, and only valid with, --role customer")

    password = getpass.getpass("Password: ")
    with get_conn() as conn:
        created = create_user(conn, args.email, password, role, args.driver_id, args.customer_id)
        conn.commit()
    print("created" if created else "account already exists")


if __name__ == "__main__":
    main()
