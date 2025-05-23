#!/usr/bin/env python
"""
Script to generate initial Alembic migration for the RFP platform
"""
import os
import subprocess
import sys

# Add the parent directory to the path so we can import the app module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def main():
    """Generate the initial migration"""
    # Generate the migration
    subprocess.run(
        ["alembic", "revision", "--autogenerate", "-m", "Initial database schema"],
        check=True,
    )
    print("Migration generated successfully!")
    
    # Apply the migration
    apply_migration = input("Do you want to apply the migration now? (y/n): ")
    if apply_migration.lower() == "y":
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        print("Migration applied successfully!")
    else:
        print("Migration not applied. Run 'alembic upgrade head' to apply.")

if __name__ == "__main__":
    main()
