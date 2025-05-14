import os
import uuid

from dotenv import load_dotenv

load_dotenv(".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")

HIVETRACE_URL = os.getenv("HIVETRACE_URL")
HIVETRACE_ACCESS_TOKEN = os.getenv("HIVETRACE_ACCESS_TOKEN")

HIVETRACE_APP_ID = os.getenv("HIVETRACE_APP_ID")
SESSION_ID = os.getenv("SESSION_ID")
USER_ID = os.getenv("USER_ID")

PLANNER_ID = str(uuid.uuid4())
WRITER_ID = str(uuid.uuid4())
EDITOR_ID = str(uuid.uuid4())
