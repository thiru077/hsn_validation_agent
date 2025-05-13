import logging
import pandas as pd
from typing import List, Dict, Union

from . import config  # Relative import for config
from .gsheet_client import fetch_data_from_google_sheet # Relative import

# Assuming ADK components are available in your environment
try:
    from google.adk.agents import Agent
except ImportError:
    logging.warning("ADK Agent component not found. Using a conceptual placeholder for Agent.")
    Agent = lambda name, model=None, description="", instruction="", tools=[]: type('Agent', (), {'name': name, 'model': model, 'description': description, 'instruction': instruction, 'tools': tools})()

HSN_DATA = pd.DataFrame(columns=['HSNCode', 'Description']) # Initialize as empty DataFrame
HSN_CODE_TO_DESCRIPTION_MAP = {}

def load_and_process_hsn_data() -> None:
    """
    Loads and processes HSN data from the Google Sheet using configurations.
    Populates global HSN_DATA and HSN_CODE_TO_DESCRIPTION_MAP.
    """
    global HSN_DATA, HSN_CODE_TO_DESCRIPTION_MAP
    
    sheet_id = config.SPREADSHEET_ID
    sheet_name = config.HSN_SHEET_NAME
    creds_path = config.SERVICE_ACCOUNT_FILE_PATH

    logging.info("LOAD_PROCESS_FUNC_ENTRY: Starting data load and process.")

    if not all([sheet_id, sheet_name, creds_path]):
        logging.error("LOAD_PROCESS_FUNC_ERROR: Spreadsheet ID, Sheet Name, or Service Account Path not configured. Cannot load HSN data.")
        HSN_DATA = pd.DataFrame(columns=['HSNCode', 'Description'])
        HSN_CODE_TO_DESCRIPTION_MAP = {}
        return

    raw_data = fetch_data_from_google_sheet(sheet_id, sheet_name, creds_path)

    if not raw_data:
        logging.error("LOAD_PROCESS_FUNC_ERROR: No data returned from fetch_data_from_google_sheet. HSN validation will use empty dataset.")
        HSN_DATA = pd.DataFrame(columns=['HSNCode', 'Description']) 
        HSN_CODE_TO_DESCRIPTION_MAP = {}
        return

    logging.info(f"LOAD_PROCESS_FUNC_INFO: {len(raw_data)} records received from fetch function.")
    if raw_data: 
        logging.info(f"LOAD_PROCESS_FUNC_INFO: First raw record for processing: {raw_data[0]}")
    
    normalized_data = []
    
    actual_hsn_column_name_in_sheet = None
    actual_desc_column_name_in_sheet = None

    if raw_data and len(raw_data) > 0:
        sheet_headers = list(raw_data[0].keys())
        logging.info(f"LOAD_PROCESS_FUNC_INFO: Actual headers from sheet: {sheet_headers}")

        # Try to find the best match for HSN column
        for header in sheet_headers:
            if header.lower().replace(" ", "").replace("_", "") == config.EXPECTED_HSN_COLUMN_KEY.lower().replace(" ", "").replace("_", ""):
                actual_hsn_column_name_in_sheet = header
                break 
        if actual_hsn_column_name_in_sheet:       
            logging.info(f"LOAD_PROCESS_FUNC_INFO: Matched HSN column in sheet to: '{actual_hsn_column_name_in_sheet}' (based on expected key '{config.EXPECTED_HSN_COLUMN_KEY}')")
        else:
            logging.warning(f"LOAD_PROCESS_FUNC_WARNING: Could not find a direct match for HSN column '{config.EXPECTED_HSN_COLUMN_KEY}' in sheet headers {sheet_headers}. Trying exact expected key.")
            actual_hsn_column_name_in_sheet = config.EXPECTED_HSN_COLUMN_KEY


        # Try to find the best match for Description column
        for header in sheet_headers:
            if header.lower().replace(" ", "").replace("_", "") == config.EXPECTED_DESC_COLUMN_KEY.lower().replace(" ", "").replace("_", ""):
                actual_desc_column_name_in_sheet = header
                break
        if actual_desc_column_name_in_sheet:
            logging.info(f"LOAD_PROCESS_FUNC_INFO: Matched Description column in sheet to: '{actual_desc_column_name_in_sheet}' (based on expected key '{config.EXPECTED_DESC_COLUMN_KEY}')")
        else:
            logging.warning(f"LOAD_PROCESS_FUNC_WARNING: Could not find a direct match for Description column '{config.EXPECTED_DESC_COLUMN_KEY}' in sheet headers {sheet_headers}. Trying exact expected key.")
            actual_desc_column_name_in_sheet = config.EXPECTED_DESC_COLUMN_KEY

    for i, row_dict in enumerate(raw_data):
        hsn_value = str(row_dict.get(actual_hsn_column_name_in_sheet, '')).strip()
        desc_value = str(row_dict.get(actual_desc_column_name_in_sheet, '')).strip()
        
        normalized_data.append({'HSNCode': hsn_value, 'Description': desc_value})

        if i < 2: # Log the first few processed rows for quick check
            logging.info(f"LOAD_PROCESS_FUNC_DEBUG: Processed row {i+1}: HSN='{hsn_value}', Desc='{desc_value}' (Used HSN Key: '{actual_hsn_column_name_in_sheet}', Used Desc Key: '{actual_desc_column_name_in_sheet}')")
            
    data_df = pd.DataFrame(normalized_data)

    if data_df.empty and len(normalized_data) > 0:
        logging.warning("LOAD_PROCESS_FUNC_WARNING: DataFrame is empty but normalized_data was not. This is unexpected.")
    elif data_df.empty:
        logging.warning("LOAD_PROCESS_FUNC_WARNING: DataFrame is empty after normalization (likely no raw_data or issues).")

    if 'HSNCode' not in data_df.columns or 'Description' not in data_df.columns:
        logging.error("LOAD_PROCESS_FUNC_CRITICAL: 'HSNCode' or 'Description' columns are missing after creating DataFrame from normalized_data.")
        HSN_DATA = pd.DataFrame(columns=['HSNCode', 'Description'])
        HSN_CODE_TO_DESCRIPTION_MAP = {}
        return

    logging.info(f"LOAD_PROCESS_FUNC_INFO: DataFrame created with {len(data_df)} rows. Columns: {data_df.columns.tolist()}")
    if not data_df.empty:
        sample_hsns = data_df[data_df['HSNCode'] != '']['HSNCode'].head().to_string()
        logging.info(f"LOAD_PROCESS_FUNC_INFO: Sample of HSNCode column values (non-empty, before further filtering): \n{sample_hsns if not sample_hsns.strip().endswith('Empty Series') else 'No non-empty HSN codes in sample.'}")
    
    initial_row_count = len(data_df)
    data_df['HSNCode_is_digit'] = data_df['HSNCode'].apply(lambda x: x.isdigit())
    data_df = data_df[(data_df['HSNCode'] != '') & (data_df['HSNCode_is_digit'])]
    rows_dropped = initial_row_count - len(data_df)
    logging.info(f"LOAD_PROCESS_FUNC_INFO: Dropped {rows_dropped} rows due to empty or non-numeric HSNCode after processing.")
    data_df = data_df.drop(columns=['HSNCode_is_digit'])

    HSN_DATA = data_df
    if not HSN_DATA.empty:
        hsn_data_for_map = HSN_DATA.dropna(subset=['HSNCode']) 
        hsn_data_for_map = hsn_data_for_map[hsn_data_for_map['HSNCode'] != ''] 
        HSN_CODE_TO_DESCRIPTION_MAP = pd.Series(hsn_data_for_map.Description.values, index=hsn_data_for_map.HSNCode).to_dict()
    else:
        logging.warning("LOAD_PROCESS_FUNC_WARNING: HSN_DATA DataFrame is empty after filtering for non-empty and numeric HSN Codes.")
        HSN_CODE_TO_DESCRIPTION_MAP = {}

    logging.info(f"LOAD_PROCESS_FUNC_SUCCESS: HSN Master Data loaded and processed. Final valid entries for map: {len(HSN_CODE_TO_DESCRIPTION_MAP)}.")
    if HSN_CODE_TO_DESCRIPTION_MAP:
        logging.info(f"LOAD_PROCESS_FUNC_SAMPLE_MAP: Sample of HSN_CODE_TO_DESCRIPTION_MAP: {dict(list(HSN_CODE_TO_DESCRIPTION_MAP.items())[:3])}")
    else:
        logging.warning("LOAD_PROCESS_FUNC_FINAL_WARNING: HSN_CODE_TO_DESCRIPTION_MAP is empty. Check logs for column name issues or empty/non-numeric HSN codes in source data.")


def validate_hsn_code_from_gsheet(hsn_codes: Union[str, List[str]]) -> List[Dict[str, str]]:
    """
    Validates one or more HSN codes against the master dataset loaded from Google Sheet.
    """
    logging.info(f"--- Tool: validate_hsn_code_from_gsheet called for: {hsn_codes} ---")
    if HSN_DATA is None or HSN_DATA.empty or not HSN_CODE_TO_DESCRIPTION_MAP:
        logging.warning("HSN Master Data from Google Sheet not loaded or is empty. Validation may be incomplete.")
        codes_to_check_list = [hsn_codes] if isinstance(hsn_codes, str) else hsn_codes
        return [{"hsn_code": str(code), "status": "error", "message": "HSN Master Data from Google Sheet not available or empty.", "description": ""} for code in codes_to_check_list]
    
    if isinstance(hsn_codes, str):
        codes_to_check = [hsn_codes.strip()]
    else:
        codes_to_check = [str(code).strip() for code in hsn_codes]
        
    results = []
    for code in codes_to_check:
        validation_result = {"hsn_code": code, "status": "invalid", "message": "", "description": ""}
        if not code: 
            validation_result["message"] = "HSN code cannot be empty."
        elif not code.isdigit(): 
            validation_result["message"] = "HSN code must be numeric."
        # Add length check if desired, e.g.:
        # elif not (2 <= len(code) <= 8 and len(code) % 2 == 0):
        #    validation_result["message"] = "HSN code length must be 2, 4, 6, or 8 digits."
        elif code in HSN_CODE_TO_DESCRIPTION_MAP:
            description = HSN_CODE_TO_DESCRIPTION_MAP[code]
            validation_result["status"] = "valid"
            validation_result["message"] = f"HSN code is valid. Description: {description}"
            validation_result["description"] = description
        else: 
            validation_result["message"] = "HSN code not found in master data."
        results.append(validation_result)
    return results

# --- Agent Definition ---
hsn_gsheet_validation_agent = Agent(
    name="hsn_direct_gsheet_validator_v1",
    model=config.GEMINI_MODEL_ID if config.GOOGLE_API_KEY else None, 
    description="Validates HSN codes using a tool that accesses a master dataset in a Google Sheet.",
    instruction="This agent contains a tool to validate HSN codes. In a direct call scenario, the instruction is for documentation.",
    tools=[validate_hsn_code_from_gsheet],
)

# --- Initial Data Load on Module Import ---
# This ensures data is loaded when agent_core is imported.
if __name__ != '__main__': # Avoid running twice if agent_core.py is run directly for tests
    load_and_process_hsn_data()