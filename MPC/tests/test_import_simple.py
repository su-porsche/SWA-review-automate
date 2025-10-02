#!/usr/bin/env python3
"""Simple test script to debug import issues."""

print("[1] Starting script...")

import sys
print("[2] Imported sys")

import json
print("[3] Imported json")

from pathlib import Path
print("[4] Imported Path")

print("[5] Attempting psycopg2 import...")
import psycopg2
print("[6] Imported psycopg2")

from psycopg2.extras import execute_values
print("[7] Imported execute_values")

print("[8] All imports successful!")

# Test DB connection
print("[9] Testing DB connection...")
try:
    conn = psycopg2.connect(
        host='localhost',
        database='swadocs',
        user='swaagent',
        password='swaagent911'
    )
    print("[10] ✓ Connected to database")
    conn.close()
except Exception as e:
    print(f"[10] ✗ Connection failed: {e}")

print("[11] Script completed successfully")
