#
# Import FastAPI to create endpoints for my app.
from fastapi import FastAPI, Request
#
#
from fastapi.templating import Jinja2Templates
#
# Import StaticFiles to instruct FastAPI where to get the static files (files
#   that my HTML references directly like CSS and JavaScript files).
from fastapi.staticfiles import StaticFiles
#
# Import HTMLResponse class to instruct FastAPI to return HTML content instead
#   of JSON by default.
from fastapi.responses import HTMLResponse
# 
# Import my classes.
from rentize import Client, Electricity

#
# Instantiate the FastAPI to a variable.
my_app = FastAPI()
# 
# Mount a folder for static files.
my_app.mount("/static", StaticFiles(directory="static"), name="static")
#
# Point FastAPI to the templates folder.
templates = Jinja2Templates(directory="templates")
#
# Home page to the app - returns a JSON object.
@my_app.get("/")
async def root():
    return {
        "message": "RENTIZE IS NOW ACCESSIBLE ON UVICORN SEVER"
    }

#
# Display the deselection table.
@my_app.get("/deselection", response_class=HTMLResponse)
def deselection_table(request: Request):
    return templates.TemplateResponse(
        "deselect.html",
        {
            "request": request
        }
    )

#
# Page that shows all the bills - returns HTML content.
@my_app.get("/all_ebills", response_class=HTMLResponse)
def all_ebills(request: Request):
    #
    # User input dates to specify period.
    month = 9
    year = 2025
    #
    # Instantiate the Client class using the dates above.
    client = Client(month, year)
    #
    # Instantiate the Electricty class using the client.
    e_class = Electricity(client)
    #
    # Get all the electricity bills DataFrame for that specified month.
    df = e_class.get_all_bills()
    #
    # Convert the DataFrame above to a HTML table.
    table_html = df.to_html(index=True)
    #
    # Pass both request and table to template
    return templates.TemplateResponse(
        "table.html",
        {
            "request": request,
            "table": table_html
        }
    )

