# Google Sheets Integration

## Overview
Google Sheets connector enables reading and writing NBA data to/from Google Sheets for collaborative analysis.

## Configuration

### Environment Variables
```bash
GOOGLE_SHEETS_CREDENTIALS_FILE=path/to/credentials.json
GOOGLE_SHEETS_SCOPES=https://www.googleapis.com/auth/spreadsheets
```

## Usage

### Writing Data to Sheets
```python
from mcp_server.google_sheets_connector import GoogleSheetsConnector

sheets = GoogleSheetsConnector(credentials_file=os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE"))
await sheets.write_data(
    spreadsheet_id="your_sheet_id",
    range="Sheet1!A1:E10",
    data=player_stats_df
)
```

### Reading Data from Sheets
```python
data = await sheets.read_data(
    spreadsheet_id="your_sheet_id",
    range="Sheet1!A1:E10"
)
```

## Testing
Run tests with:
```bash
pytest tests/test_google_sheets.py
```

## Features
- Batch data import/export
- Real-time collaboration
- Formula preservation
- Automatic type conversion
- Formatting support
- Multi-sheet operations

## Dependencies
- google-auth>=2.23.0
- google-auth-oauthlib>=1.1.0
- google-auth-httplib2>=0.1.1
- google-api-python-client>=2.100.0

## Setup
1. Enable Google Sheets API in Google Cloud Console
2. Download credentials.json
3. Set GOOGLE_SHEETS_CREDENTIALS_FILE path
4. First run will open browser for OAuth authorization

