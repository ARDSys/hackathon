from pathlib import Path

from dotenv import load_dotenv

env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    load_dotenv(env_file)
else:
    raise FileNotFoundError(
        f"Environment file {env_file} not found. Please create it with the necessary variables."
    )
