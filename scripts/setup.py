"""
Setup script for initial project configuration
"""

import os
import sys
from pathlib import Path
import shutil

# Project root
PROJECT_ROOT = Path(__file__).parent.parent


def create_directories():
    """Create necessary directories"""
    directories = [
        "data/uploads",
        "data/outputs",
        "data/outputs/tasks",
        "data/chroma_db",
        "models/cache",
        "logs",
        "tests/fixtures"
    ]
    
    print("Creating project directories...")
    for dir_path in directories:
        full_path = PROJECT_ROOT / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {dir_path}")


def setup_env_file():
    """Setup environment configuration file"""
    env_example = PROJECT_ROOT / "config.env.example"
    env_file = PROJECT_ROOT / "config.env"
    
    if env_file.exists():
        print(f"⚠️  config.env already exists, skipping...")
        return
    
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ Created config.env from example")
        print("⚠️  Please edit config.env and add your API keys!")
    else:
        print("❌ config.env.example not found")


def create_gitkeep_files():
    """Create .gitkeep files in empty directories"""
    directories = [
        "data/uploads",
        "data/outputs",
        "models/cache",
        "logs"
    ]
    
    print("\nCreating .gitkeep files...")
    for dir_path in directories:
        gitkeep_path = PROJECT_ROOT / dir_path / ".gitkeep"
        gitkeep_path.touch()
        print(f"✅ Created: {dir_path}/.gitkeep")


def check_python_version():
    """Check Python version"""
    print("\nChecking Python version...")
    if sys.version_info < (3, 11):
        print("⚠️  Python 3.11+ is recommended")
        print(f"   Current version: {sys.version}")
    else:
        print(f"✅ Python version: {sys.version}")


def main():
    """Run setup"""
    print("=" * 60)
    print("Meeting Intelligence Platform - Setup")
    print("=" * 60)
    print()
    
    check_python_version()
    print()
    
    create_directories()
    print()
    
    setup_env_file()
    print()
    
    create_gitkeep_files()
    print()
    
    print("=" * 60)
    print("Setup complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Edit config.env with your API keys")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Download models: python scripts/download_models.py")
    print("4. Run API: uvicorn src.api.main:app --reload")
    print("5. Run Frontend: streamlit run src/frontend/app.py")
    print()


if __name__ == "__main__":
    main()

