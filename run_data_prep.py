"""
Script to run all data preparation steps for AI Agent Insure project.
Creates insureds.db and Chroma vector store in one command.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
INSURED_DB_SCRIPT = ROOT / "insured-db" / "create_and_seed_insureds_db.py"
VECTOR_STORE_SCRIPT = ROOT / "vector-store" / "create_chroma_vectorstore.py"

steps = [
    ("Creating insureds.db (structured data)", [sys.executable, str(INSURED_DB_SCRIPT)]),
    ("Creating Chroma vector store (unstructured data)", [sys.executable, str(VECTOR_STORE_SCRIPT)]),
]

def main():
    for desc, cmd in steps:
        print(f"\n=== {desc} ===")
        try:
            result = subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running {desc}: {e}")
            sys.exit(1)
    print("\nAll data preparation steps completed successfully.")

if __name__ == "__main__":
    main()
