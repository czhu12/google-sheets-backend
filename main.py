import os
from typing import Union
import gspread
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

load_dotenv()
SERVICE_ACCOUNT_EMAIL = os.getenv("SERVICE_ACCOUNT_EMAIL")

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/public", StaticFiles(directory="public"), name="public")

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "service_account_email": SERVICE_ACCOUNT_EMAIL})

@app.get("/sheet/{sheet_id}/{sheet_name}")
def read_sheet(sheet_id: str, sheet_name: str):
    gc = gspread.service_account('./credentials/personal-310102-924dafe7cd38.json')
    print("sheet_id", sheet_id)
    print("sheet_name", sheet_name)
    sht1 = gc.open_by_key(sheet_id)
    sheet = sht1.worksheet(sheet_name)
    data = sheet.get_all_values()
    
    headers = data[0]
    rows = data[1:]
    return {"data": [dict(zip(headers, row)) for row in rows]}

