import logging
import os
from typing import List, Dict, Any
import gspread
from google.oauth2.service_account import Credentials

from . import config # Use relative import for config

def fetch_data_from_google_sheet(sheet_id: str, sheet_name: str, creds_path: str) -> List[Dict[str, Any]]:
    """
    Fetches data from the specified Google Sheet using service account credentials.
    Returns a list of dictionaries, where each dictionary represents a row.
    """
    logging.info(f"FETCH_FUNC_ENTRY: Attempting to fetch data from Google Sheet ID: {sheet_id}, Name: {sheet_name}, Creds: {creds_path}")
    if not creds_path or not os.path.exists(creds_path):
        logging.error(f"FETCH_FUNC_ERROR: Service account file not found at {creds_path}. Cannot fetch from Google Sheets.")
        return []
    if not sheet_id or not sheet_name:
        logging.error("FETCH_FUNC_ERROR: Spreadsheet ID or Sheet Name is missing. Cannot fetch from Google Sheets.")
        return[]

    try:
        logging.info("FETCH_FUNC_INFO: Setting up GSheet credentials and client.")
        scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
        credentials = Credentials.from_service_account_file(creds_path, scopes=scopes)
        gc = gspread.authorize(credentials)
        
        logging.info(f"FETCH_FUNC_INFO: Opening spreadsheet by key: {sheet_id}")
        spreadsheet = gc.open_by_key(sheet_id)
        logging.info(f"FETCH_FUNC_INFO: Opening worksheet by name: {sheet_name}")
        worksheet = spreadsheet.worksheet(sheet_name)
        logging.info("FETCH_FUNC_INFO: Getting all records from worksheet.")
        list_of_hashes = worksheet.get_all_records(empty_value='') # Ensure empty cells are read as empty strings
        
        logging.info(f"FETCH_FUNC_SUCCESS: Successfully fetched {len(list_of_hashes)} records from Google Sheet: '{sheet_name}'.")
        if list_of_hashes and len(list_of_hashes) > 0:
            logging.info(f"FETCH_FUNC_SAMPLE_RECORD: First fetched record: {list_of_hashes[0]}")
        return list_of_hashes
    except gspread.exceptions.SpreadsheetNotFound:
        logging.error(f"FETCH_FUNC_ERROR: Spreadsheet with ID '{sheet_id}' not found or not shared with the service account.")
        return []
    except gspread.exceptions.WorksheetNotFound:
        logging.error(f"FETCH_FUNC_ERROR: Worksheet with name '{sheet_name}' not found in spreadsheet ID '{sheet_id}'.")
        return []
    except Exception as e:
        logging.error(f"FETCH_FUNC_ERROR: An unexpected error occurred while fetching data from Google Sheet: {e}", exc_info=True)
        return []