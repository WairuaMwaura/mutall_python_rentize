#
# Import FastAPI to create endpoints for my app.
from fastapi import FastAPI, Request, Query
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
# Anytime someone visits /static/... in the browser, serve them files from this folder.
# It creates an actual route (/static) in the app.
my_app.mount("/static", StaticFiles(directory="static"), name="static")
#
# Point FastAPI to the templates folder.
# When I want to render an HTML page, go look for template files inside this folder.
# The app will load index.html from the templates/ folder, render it (fill placeholders, variables), then serve it to the user.
templates = Jinja2Templates(directory="templates")
#
# Home page to the app - returns a HTML page.
@my_app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request
        }
    )
    
# 
# Display electricity page in 2 modes: 
#   1. initial load and 
#   2. with user generating tables (i.e., all_ebills, client_ebills etc).
@my_app.get("/electricity", response_class=HTMLResponse, name="electricity_page")
async def electricity(request: Request, month: int | None = None, year: int = None):
    #
    # Initialize ebills_table, client_ebills_table, unattended_ebills_table,
    #   service_ebills_table to None for the initial page load.
    ebills_table = None
    client_ebills_table = None
    unattended_ebills_table = None
    service_ebills_table = None
    #
    # If client generates all bills with month and year values.
    if (month != None and year != None):
        #
        # Instantiate the Client class using the dates above.
        client = Client(month, year)
        #
        # Instantiate the Electricty class using the client.
        e_class = Electricity(client)
        #
        # Get all the electricity bills DataFrame for that specified month.
        ebills_df = e_class.get_all_bills()
        #
        # Convert the DataFrame above to a HTML table.
        ebills_table = ebills_df.to_html(index=True)
        #
        # Get all the client electricity bills DataFrame for that specified month.
        client_ebills_df = e_class.get_client_ebills()
        #
        # Convert the DataFrame above to a HTML table.
        client_ebills_table = client_ebills_df.to_html(index=True)
        #
        # Get all the unattended electricity bills DataFrame for that specified month.
        unattended_ebills_df = e_class.get_unattended_ebills()
        #
        # Convert the DataFrame above to a HTML table.
        unattended_ebills_table = unattended_ebills_df.to_html(index=True)
        #
        # Get all the service electricity bills DataFrame for that specified month.
        service_ebills_df = e_class.get_service_ebills()
        #
        # Convert the DataFrame above to a HTML table.
        service_ebills_table = service_ebills_df.to_html(index=True)
    #
    # Pass both request and all the ebill tables to electricity.html template.
    return templates.TemplateResponse(
        "electricity.html",
        {
            "request": request,
            "ebills": ebills_table,
            "client_ebills": client_ebills_table,
            "unattended_ebills": unattended_ebills_table,
            "service_ebills": service_ebills_table
        }
    )

