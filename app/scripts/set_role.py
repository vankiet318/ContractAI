"""
Give a user the admin role, or take it away. The first admin has to be
made this way; after that, admins can change roles from the dashboard.

Run inside the backend container:
    docker compose exec backend python -m app.scripts.set_role <email> admin
    docker compose exec backend python -m app.scripts.set_role <email> user
"""

import argparse
import sys

from app.auth.repository import UserRepository


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("email")
    parser.add_argument("role", choices=["admin", "user"])
    args = parser.parse_args()

    repository = UserRepository()
    user = repository.get_by_email(args.email)

    if user is None:
        sys.exit(f"No user with email {args.email}")

    repository.update_role(user.user_id, args.role)

    print(f"{user.email} is now {args.role}")


if __name__ == "__main__":
    main()
