#!/usr/bin/env python3
"""Interactive DB connection tester.

Usage: python test_db.py
It will read DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASS from environment if present,
otherwise it will prompt. Then it calls db.test_connection() and prints a helpful
error message if connection fails.
"""
import os
from getpass import getpass

def prompt_env(name, default=None, secret=False):
    val = os.getenv(name)
    if val:
        return val
    prompt = f"{name} [{default}]> " if default else f"{name}> "
    if secret:
        v = getpass(prompt)
    else:
        v = input(prompt)
    return v or (default or "")


def main():
    host = prompt_env('DB_HOST', 'localhost')
    port = prompt_env('DB_PORT', '5432')
    name = prompt_env('DB_NAME', 'postgres')
    user = prompt_env('DB_USER')
    pwd = prompt_env('DB_PASS', secret=True)

    os.environ['DB_HOST'] = host
    os.environ['DB_PORT'] = port
    os.environ['DB_NAME'] = name
    if user:
        os.environ['DB_USER'] = user
    if pwd:
        os.environ['DB_PASS'] = pwd

    try:
        from db import test_connection
    except Exception as e:
        print('Failed to import db module or driver not installed:')
        print(e)
        return

    try:
        ok = test_connection()
        if ok:
            print('Success: connected to the database with provided settings')
        else:
            print('test_connection returned False (unexpected)')
    except Exception as e:
        print('Connection failed:')
        print(e)
        print('\nCommon fixes:')
        print('- Ensure Postgres server is running and reachable (check `psql` or `brew services list`)')
        print("- Make sure the DB user exists. You can create a user and DB via psql:\n  CREATE USER myuser WITH PASSWORD 'pass';\n  CREATE DATABASE mydb OWNER myuser;")
        print("- Or set the environment variables DB_USER and DB_PASS to an existing Postgres role")


if __name__ == '__main__':
    main()

