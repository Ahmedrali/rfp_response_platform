#!/usr/bin/env python
"""
Script to test database connection for SQLAlchemy
"""
import os
import sys

# Add the parent directory to the path so we can import the app module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import psycopg2
from sqlalchemy import create_engine
from app.utils.config import settings

def test_connection():
    """Test database connection"""
    print(f"Testing connection to: {settings.DATABASE_URL}")
    
    # Create explicit connection string
    db_parts = settings.DATABASE_URL.replace("+asyncpg", "").split("://")
    if len(db_parts) == 2:
        driver, rest = db_parts
        if "?" in rest:
            rest = rest.split("?")[0]  # Remove query parameters
        
        if "@" in rest:
            auth, location = rest.split("@")
            user_pass, host_port_db = auth, location
            if ":" in user_pass:
                user, password = user_pass.split(":")
            else:
                user, password = user_pass, ""
                
            if "/" in host_port_db:
                host_port, dbname = host_port_db.split("/")
                if ":" in host_port:
                    host, port = host_port.split(":")
                else:
                    host, port = host_port, "5432"
                    
                conn_str = f"host={host} port={port} dbname={dbname} user={user} password={password}"
                print(f"Using connection params: {conn_str}")
                
                # Test raw psycopg2 connection
                print("\nTesting direct psycopg2 connection...")
                try:
                    conn = psycopg2.connect(conn_str)
                    print("Successfully connected with psycopg2!")
                    conn.close()
                except Exception as e:
                    print(f"Error connecting with psycopg2: {e}")
                
                # Test SQLAlchemy connection
                print("\nTesting SQLAlchemy connection...")
                try:
                    engine = create_engine(f"postgresql://{user}:{password}@{host}:{port}/{dbname}")
                    conn = engine.connect()
                    print("Successfully connected with SQLAlchemy!")
                    conn.close()
                    engine.dispose()
                except Exception as e:
                    print(f"Error connecting with SQLAlchemy: {e}")
            else:
                print("Could not parse database name")
        else:
            print("Could not parse authentication info")
    else:
        print("Invalid database URL format")

if __name__ == "__main__":
    test_connection()
