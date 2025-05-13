import asyncio
import logging
import os # For genai API key check

# Configure logging for this script
logging.basicConfig(level=logging.INFO)

# Import agent and specific configurations from the app package
from app import config # This will load .env
from app.agent_core import hsn_gsheet_validation_agent, HSN_CODE_TO_DESCRIPTION_MAP, validate_hsn_code_from_gsheet, load_and_process_hsn_data
import google.generativeai as genai

def initial_setup_and_checks():
    """Performs initial setup and prints configuration details."""
    if config.GOOGLE_API_KEY:
        try:
            genai.configure(api_key=config.GOOGLE_API_KEY)
            logging.info("Gemini API Key configured for run.py.")
        except Exception as e:
            logging.error(f"Error configuring Gemini API: {e}")
    else:
        logging.warning("GOOGLE_API_KEY not found. Gemini model features in agent might be limited.")

    if not (config.SERVICE_ACCOUNT_FILE_PATH and os.path.exists(config.SERVICE_ACCOUNT_FILE_PATH)):
        logging.error(f"Service account file not found at: {config.SERVICE_ACCOUNT_FILE_PATH}. Google Sheets connection will fail.")
    
    logging.info(f"Spreadsheet ID from config: {config.SPREADSHEET_ID}")
    logging.info(f"Sheet Name from config: {config.HSN_SHEET_NAME}")
    logging.info(f"Expected HSN Column from config: '{config.EXPECTED_HSN_COLUMN_KEY}'")
    logging.info(f"Expected Description Column from config: '{config.EXPECTED_DESC_COLUMN_KEY}'")
    logging.info(f"Using Gemini Model ID (if applicable): {config.GEMINI_MODEL_ID}")
    logging.info(f"Agent Name: {hsn_gsheet_validation_agent.name}")


async def call_agent_tool_directly(query: str, agent_instance):
    """
    Simulates sending a query to an agent and directly calling its first tool.
    """
    logging.info(f"\n>>> User Query to {agent_instance.name} (direct tool call): {query}")

    if not agent_instance.tools:
        logging.error(f"Agent {agent_instance.name} has no tools registered.")
        return "Agent has no tools to process this query."

    tool_to_call = agent_instance.tools[0] 

    # Simplified HSN code extraction
    potential_hsns = [word.strip(',.').strip() for word in query.split() if word.strip(',.').strip().isdigit()]
    if not potential_hsns: 
        cleaned_query_parts = [q.strip() for q in query.replace("validate HSN codes", "", 1).replace("validate HSN code", "", 1).replace("validate", "", 1).replace("check HSN codes", "", 1).replace("check HSN", "", 1).split("and")]
        potential_hsns = [part.strip() for part in cleaned_query_parts if part.strip().isdigit()]
        if not potential_hsns and query.strip().isdigit(): 
            potential_hsns = [query.strip()]

    if not potential_hsns:
        logging.warning(f"Could not extract HSN codes from query: '{query}'. Calling tool with the original query as input.")
        tool_input = query 
    elif len(potential_hsns) == 1:
        tool_input = potential_hsns[0]
    else:
        tool_input = potential_hsns
    
    logging.info(f"Extracted HSN(s) for tool '{tool_to_call.__name__}': {tool_input}")
    
    try:
        tool_result = tool_to_call(tool_input) # Direct call to the validation function
        response_text = f"Tool '{tool_to_call.__name__}' called with '{tool_input}'. Result:\n"
        if isinstance(tool_result, list):
            for res_item in tool_result:
                response_text += f"  HSN: {res_item.get('hsn_code', 'N/A')}, Status: {res_item.get('status', 'N/A')}, Message: {res_item.get('message', 'N/A')}\n"
        else:
            response_text += f"  Unexpected tool result format: {tool_result}\n"
    except Exception as e:
        logging.error(f"Error calling tool {tool_to_call.__name__}: {e}", exc_info=True)
        response_text = f"Error executing HSN validation tool: {e}"

    logging.info(f"<<< Agent {agent_instance.name} (direct tool call) Response:\n{response_text}")
    return response_text


async def main_direct_tool_interactions():
    """Runs example interactions by directly calling the agent's tool."""
    logging.info(f"Starting direct tool call interactions for agent: {hsn_gsheet_validation_agent.name}")

    # Data loading is now handled when agent_core is imported,
    # but we check HSN_CODE_TO_DESCRIPTION_MAP to see if it was successful.
    if not HSN_CODE_TO_DESCRIPTION_MAP:
        if not all([config.SPREADSHEET_ID, config.HSN_SHEET_NAME, config.SERVICE_ACCOUNT_FILE_PATH, os.path.exists(config.SERVICE_ACCOUNT_FILE_PATH or "")]):
             logging.error("\nHSN Master data from Google Sheet could not be loaded due to configuration issues (check .env and service account file path).")
        else:
            logging.error("\nHSN Master data from Google Sheet is empty after attempting load. Check sheet content, sharing, and logs for processing errors (especially column names in app/config.py or .env).")
        
        await call_agent_tool_directly("Query when data map is empty post-load", hsn_gsheet_validation_agent)
        return

    # Test with HSN codes you expect to be in your sheet
    # Example: if '0101' and '02021000' are valid and '0303' might be too.
    await call_agent_tool_directly("Validate HSN 0101", hsn_gsheet_validation_agent) 
    await call_agent_tool_directly("Check HSN codes 02021000 and 99987 and 0303", hsn_gsheet_validation_agent)
    await call_agent_tool_directly("Is XYZ99 an HSN code?", hsn_gsheet_validation_agent) 
    await call_agent_tool_directly("01011010", hsn_gsheet_validation_agent) 
    await call_agent_tool_directly("Validate HSN codes 01, 0202, 03031300", hsn_gsheet_validation_agent)
    await call_agent_tool_directly("85171211", hsn_gsheet_validation_agent) # Add a specific code to test from your sheet


if __name__ == "__main__":
    initial_setup_and_checks() # Perform setup and print config
    
    # Reload data in case run.py is executed after some changes or as the main entry.
    # agent_core.py also loads data on import. This is a bit redundant but ensures it if run.py is the sole entry.
    # Consider a more sophisticated data loading strategy for larger apps (e.g., lazy loading or explicit init).
    if not HSN_CODE_TO_DESCRIPTION_MAP: # If map is still empty, try loading again.
        logging.info("HSN map empty, attempting data load from run.py...")
        load_and_process_hsn_data()


    logging.info("\nStarting Direct Tool Call async interactions...")
    try:
        loop = asyncio.get_running_loop()
        if loop.is_running():
            logging.info("Asyncio loop is already running. Creating task for main_direct_tool_interactions.")
            # This is suitable if run.py is imported and its main() is called from an existing loop
            asyncio.ensure_future(main_direct_tool_interactions()) 
        else: # Should not happen if get_running_loop succeeded without RuntimeError
            logging.info("Running main_direct_tool_interactions in existing loop via run_until_complete (unusual state).")
            loop.run_until_complete(main_direct_tool_interactions())
    except RuntimeError: # No current event loop
        logging.info("No current asyncio event loop. Creating a new one.")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main_direct_tool_interactions())