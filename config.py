import os
from dotenv import load_dotenv

# Load variables from .env file located in the project root
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env') # Points to root .env
load_dotenv(dotenv_path=dotenv_path)

# --- API and Service Configurations ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SERVICE_ACCOUNT_FILE_PATH = os.getenv("SERVICE_ACCOUNT_FILE_PATH")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
HSN_SHEET_NAME = os.getenv("HSN_SHEET_NAME")
GEMINI_MODEL_ID = os.getenv("GEMINI_MODEL_ID", "gemini-1.5-flash-latest")

EXPECTED_HSN_COLUMN_KEY = os.getenv("EXPECTED_HSN_COLUMN_IN_SHEET", "HSNCode")
EXPECTED_DESC_COLUMN_KEY = os.getenv("EXPECTED_DESC_COLUMN_IN_SHEET", "Description")

# --- Path to Service Account File (resolved to be absolute if relative to project root) ---
if SERVICE_ACCOUNT_FILE_PATH and not os.path.isabs(SERVICE_ACCOUNT_FILE_PATH):
    # Assuming SERVICE_ACCOUNT_FILE_PATH in .env is relative to project root
    project_root = os.path.dirname(os.path.dirname(__file__))
    SERVICE_ACCOUNT_FILE_PATH = os.path.join(project_root, SERVICE_ACCOUNT_FILE_PATH)

# --- Logging Configuration (Basic) ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
