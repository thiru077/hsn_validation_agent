## Prerequisites
-   Python 3.7+
-   A Google Cloud Project with:
    -   Google Sheets API enabled.
    -   A Service Account created with permissions to read from Google Sheets. Download its JSON key file.
-   A Google Sheet containing HSN master data, shared with the Service Account's email address (with at least "Viewer" permission). The sheet should have columns for HSN codes and their descriptions.

## Setup
1.  **Clone the Repository** (if this were a Git repo):
    ```bash
    # git clone <repository_url>
    # cd hsn_validation_agent
    ```
    If not a repo, create the `hsn_validation_agent` directory and the file structure manually.

2.  **Create a Virtual Environment** (recommended):
    ```bash
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Service Account Key File:**
    Place your downloaded Google Service Account JSON key file in the root directory of the project (e.g., `hsn_validation_agent/your-service-account-file.json`).

5.  **Create and Configure `.env` File:**
    Create a file named `.env` in the project root (`hsn_validation_agent/`) and populate it with your specific details. Use the following template:

    ```env
    GOOGLE_API_KEY=YOUR_ACTUAL_GEMINI_API_KEY_HERE
    SERVICE_ACCOUNT_FILE_PATH=your-service-account-file.json # e.g., gen-lang-client-0124330681-6d038144b4f6.json
    SPREADSHEET_ID=your_google_spreadsheet_id_here
    HSN_SHEET_NAME=your_sheet_name_with_hsn_data # e.g., HSN_MSTR or Sheet1

    # Optional: For Gemini model if used by the agent (conceptual ADK)
    GEMINI_MODEL_ID=gemini-1.5-flash-latest

    # Optional: Override default expected column names if your Google Sheet uses different headers
    # These should be the EXACT header names in your Google Sheet's first row.
    # EXPECTED_HSN_COLUMN_IN_SHEET=HSN Number
    # EXPECTED_DESC_COLUMN_IN_SHEET=Product Description
    ```

6.  **Share Google Sheet:**
    Ensure the Google Sheet specified by `SPREADSHEET_ID` is shared with the `client_email` found in your service account JSON key file. Grant at least "Viewer" permissions.

## Configuration Details
The application relies on the `.env` file for its primary configuration:
-   `GOOGLE_API_KEY`: Your API key for Google Generative AI (Gemini), used if the agent's model is enabled.
-   `SERVICE_ACCOUNT_FILE_PATH`: The filename of your Google Service Account JSON key file (assumed to be in the project root).
-   `SPREADSHEET_ID`: The ID of your Google Sheet containing HSN data.
-   `HSN_SHEET_NAME`: The name of the specific sheet (tab) within your Google Spreadsheet that holds the HSN data.
-   `GEMINI_MODEL_ID`: Specifies the Gemini model to be used (if the agent leverages LLM capabilities, which is minimal in this direct-tool-call version).
-   `EXPECTED_HSN_COLUMN_IN_SHEET` (Optional in `.env`): If your HSN code column in the Google Sheet is not named "HSNCode" (case-insensitive match), set this variable to the exact header name.
-   `EXPECTED_DESC_COLUMN_IN_SHEET` (Optional in `.env`): If your description column is not named "Description" (case-insensitive match), set this variable to the exact header name.

The script will attempt to find columns matching "HSNCode" and "Description" (case-insensitively, ignoring spaces and underscores) if the specific `.env` overrides are not provided. Check the logs for details on which columns were matched.

## Running the Agent
To run the example interactions:
```bash
python run.py