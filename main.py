import os
from typing import Union
import gspread
from fastapi import FastAPI
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
    return {"data": [dict(zip(headers, row)) for row in rows]}

