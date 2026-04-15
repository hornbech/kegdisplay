#!/usr/bin/env python3
"""Run this to generate your ADMIN_PASSWORD_HASH for .env"""
import sys
from passlib.context import CryptContext

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python hash_password.py <your_password>")
        sys.exit(1)
    ctx = CryptContext(schemes=["bcrypt"])
    print(ctx.hash(sys.argv[1]))
