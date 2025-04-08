import os
from typing import Union
import gspread
from fastapi import FastAPI, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import json
import base64

load_dotenv()
SERVICE_ACCOUNT_EMAIL = os.getenv("SERVICE_ACCOUNT_EMAIL")
CREDENTIALS_JSON = json.loads(base64.b64decode(os.getenv("CREDENTIALS_JSON_BASE64")).decode('utf-8'))

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
templates = Jinja2Templates(directory="templates")
app.mount("/public", StaticFiles(directory="public"), name="public")
gc = gspread.service_account_from_dict(CREDENTIALS_JSON)

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "service_account_email": SERVICE_ACCOUNT_EMAIL})


@app.get("/sheet/{sheet_id}/{sheet_name}")
def read_sheet(sheet_id: str, sheet_name: str):
    sht1 = gc.open_by_key(sheet_id)
    sheet = sht1.worksheet(sheet_name)
    data = sheet.get_all_values()
    
    headers = data[0]
    rows = data[1:]
    return {"data": [{"id": i+1, **dict(zip(headers, row))} for i, row in enumerate(rows)]}


@app.put("/sheet/{sheet_id}/{sheet_name}/{row_id}")
def update_sheet(sheet_id: str, sheet_name: str, row_id: int, data: dict):
    sht1 = gc.open_by_key(sheet_id)
    sheet = sht1.worksheet(sheet_name)
    
    # Get headers and current data
    all_data = sheet.get_all_values()
    headers = all_data[0]
    rows = all_data[1:]
    
    # Validate row_id
    if row_id < 1 or row_id > len(rows):
        raise HTTPException(status_code=404, detail="Row not found")
    
    # Update the row
    row_index = row_id + 1  # +1 for header row, +1 for 1-based indexing
    for col, header in enumerate(headers):
        if header in data:
            sheet.update_cell(row_index, col + 1, data[header])
    
    return {"id": row_id, **data}


@app.post("/sheet/{sheet_id}/{sheet_name}")
def create_sheet(sheet_id: str, sheet_name: str, data: dict):
    sht1 = gc.open_by_key(sheet_id)
    sheet = sht1.worksheet(sheet_name)
    
    # Get headers
    headers = sheet.row_values(1)
    
    # Prepare new row data
    new_row = []
    for header in headers:
        new_row.append(data.get(header, ""))
    
    # Append new row
    sheet.append_row(new_row)
    
    # Get the new row's ID (last row number)
    row_count = len(sheet.get_all_values())
    return {"id": row_count - 1, **data}


@app.delete("/sheet/{sheet_id}/{sheet_name}/{row_id}")
def delete_sheet(sheet_id: str, sheet_name: str, row_id: int):
    sht1 = gc.open_by_key(sheet_id)
    sheet = sht1.worksheet(sheet_name)
    
    headers = sheet.row_values(1)
    # Read the data at row_id
    row_data = sheet.row_values(row_id)
    sheet.delete_rows(row_id)
    return {"id": row_id, **dict(zip(headers, row_data))}
