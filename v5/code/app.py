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
# Import HTMLResponse (i.e., html tables) or PlainTextResponse (for access and
# error logs) class to instruct FastAPI to return HTML content instead of JSON
# by default.
from fastapi.responses import HTMLResponse, PlainTextResponse
#
# Import os to work with file paths
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 
# Import my classes.
from rentize import Client, Electricity
#
# Import datetime to select date values.
from datetime import datetime
import calendar
#
# Instantiate the FastAPI to a variable.
# my_app = FastAPI(root_path="/joshua")
my_app = FastAPI(root_path="/rentize")
#
# Mount a folder for static files. 
# Anytime someone visits /static/... in the browser, serve them files from this folder.
# It creates an actual route (/static) in the app.
my_app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "../static")), name="static")
#
# Point FastAPI to the templates folder.
# When I want to render an HTML page, go look for template files inside this folder.
# The app will load index.html from the templates/ folder, render it (fill placeholders, variables), then serve it to the user.
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
#
# Add this helper to inject static base into every template
STATIC_BASE = "/rentize/static"
#
# Home page to the app - returns a HTML page.
@my_app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "static_base": STATIC_BASE
        }
    )
  
# 
# Display electricity page  with current bills displayed by default (i.e.,
#   all_ebills, client_ebills etc).
@my_app.get("/electricity", response_class=HTMLResponse, name="electricity_page")
async def electricity(request: Request):
    #
    # Get current date and time.
    today = datetime.today()
    #
    # Extract month and year.
    month = today.month
    year = today.year
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
    # Get the number of rows in the DataFrame
    num_rows = ebills_df.shape[0]
    #
    # Convert the DataFrame above to a HTML table.
    ebills_table = ebills_df.to_html(index=False, classes="table")
    #
    # Define the structure of the HTML to be sent to the template.
    html_content = f"""
            <h2>All Electricity Bills for {calendar.month_name[month]} {year} </h2>
            <h3>Total entries {num_rows}</h3>
            {ebills_table}
        """
    #
    # Get the current clients electricity bills DataFrame for that specified month.
    client_ebills_df = e_class.get_client_ebills()
    #
    # Get the number of rows in the DataFrame
    client_num = client_ebills_df.shape[0]
    #
    # Convert the DataFrame above to a HTML table.
    client_ebills_table = client_ebills_df.to_html(index=False, classes="table")
    #
    # Define the structure of the HTML to be sent to the template.
    client_html_content = f"""
                <h2>Client Electricity Bills for {calendar.month_name[month]} {year} </h2>
                <h3>Total entries {client_num}</h3>
                {client_ebills_table}
            """
    
    return templates.TemplateResponse(
            "electricity.html",
            {
                "request": request,
                "static_base": STATIC_BASE,
                "current_ebills": html_content,
                "client_ebills": client_html_content
            }
        )

# 
# Endpoint to generate all the electricity bills.
@my_app.post("/all_ebills", response_class=HTMLResponse)
async def all_ebills(request: Request):
    #
    # Read incoming JSON data.
    data: dict = await request.json()
    #
    # Extract month and year from JSON
    month_str = data.get("month")
    year_str = data.get("year")
    # 
    # Convert the string input to integer.
    month = int(month_str)
    year = int(year_str)
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
    # Get the number of rows in the DataFrame
    num_rows = ebills_df.shape[0]
    #
    # Convert the DataFrame above to a HTML table.
    ebills_table = ebills_df.to_html(index=False, classes="table")
    # 
    # Define the structure of the HTML to be sent to the template.
    html_content = f"""
        <h2>All Electricity Bills for {calendar.month_name[month]} {year}</h2>
        <h3>Total entries {num_rows}</h3>
        {ebills_table}
    """
        
    return HTMLResponse(content = html_content)


#
# Endpoint to generate client electricity bills.
@my_app.post("/client_ebills", response_class=HTMLResponse)
async def client_ebills(request: Request):
    #
    # Read incoming JSON data.
    data: dict = await request.json()
    #
    # Extract month and year from JSON
    month_str = data.get("month")
    year_str = data.get("year")
    #
    # Convert the string input to integer.
    month = int(month_str)
    year = int(year_str)
    #
    # Instantiate the Client class using the dates above.
    client = Client(month, year)
    #
    # Instantiate the Electricty class using the client.
    e_class = Electricity(client)
    #
    # Get the client electricity bills DataFrame for that specified month.
    client_ebills_df = e_class.get_client_ebills()
    #
    # Get the number of rows in the DataFrame
    num_rows = client_ebills_df.shape[0]
    #
    # Convert the DataFrame above to a HTML table.
    client_ebills_table = client_ebills_df.to_html(index=False, classes="table")
    #
    # Define the structure of the HTML to be sent to the template.
    html_content = f"""
        <h2>Client Electricity Bills for {calendar.month_name[month]} {year}</h2>
        <h3>Total entries {num_rows}</h3>
        {client_ebills_table}
    """

    return HTMLResponse(content=html_content)


#
# Endpoint to generate unattended electricity bills.
@my_app.post("/unattended_ebills", response_class=HTMLResponse)
async def unattended_ebills(request: Request):
    #
    # Read incoming request JSON data.
    data: dict = await request.json()
    #
    # Extract month and year from JSON
    month_str = data.get("month")
    year_str = data.get("year")
    #
    # Convert the string input to integer.
    month = int(month_str)
    year = int(year_str)
    #
    # Instantiate the Client class using the dates above.
    client = Client(month, year)
    #
    # Instantiate the Electricty class using the client.
    e_class = Electricity(client)
    #
    # Get the unattended electricity bills DataFrame for that specified month.
    unattended_ebills_df = e_class.get_unattended_ebills()
    #
    # Get the number of rows in the DataFrame
    num_rows = unattended_ebills_df.shape[0]
    #
    # Convert the DataFrame above to a HTML table.
    unattended_ebills_table = unattended_ebills_df.to_html(index=False, classes="table")
    #
    # Define the structure of the HTML to be sent to the template.
    html_content = f"""
        <h2>Unattended Electricity Bills for {calendar.month_name[month]} {year}</h2>
        <h3>Total entries {num_rows}</h3>
        {unattended_ebills_table}
    """

    return HTMLResponse(content=html_content)

#
# Endpoint to generate service electricity bills.
@my_app.post("/service_ebills", response_class=HTMLResponse)
async def service_ebills(request: Request):
    #
    # Read incoming JSON data.
    data: dict = await request.json()
    #
    # Extract month and year from JSON
    month_str = data.get("month")
    year_str = data.get("year")
    #
    # Convert the string input to integer.
    month = int(month_str)
    year = int(year_str)
    #
    # Instantiate the Client class using the dates above.
    client = Client(month, year)
    #
    # Instantiate the Electricty class using the client.
    e_class = Electricity(client)
    #
    # Get the service electricity bills DataFrame for that specified month.
    service_ebills_df = e_class.get_service_ebills()
    #
    # Get the number of rows in the DataFrame
    num_rows = service_ebills_df.shape[0]
    #
    # Convert the DataFrame above to a HTML table.
    service_ebills_table = service_ebills_df.to_html(index=False, classes="table")
    #
    # Define the structure of the HTML to be sent to the template.
    html_content = f"""
        <h2>Service Electricity Bills for {calendar.month_name[month]} {year}</h2>
        <h3>Total entries {num_rows}</h3>
        {service_ebills_table}
    """

    return HTMLResponse(content=html_content)

#
# Endpoint to read error and access logs
@my_app.get("/logs/{log_type}", response_class=PlainTextResponse)
async def read_log(log_type: str):
    #
    # Get the directory where this Python file (i.e., app.py) is located
    # __file__ is the path to the current Python file
    # os.path.dirname() extracts just the directory part of that path
    # Join the directory path (i.e., "v/code/logs/")
    logs_dir: str = os.path.join(os.path.dirname(__file__), "logs")
    #
    # Create the full path to the access.log file
    # os.path.join() combines directory path and filename properly (i.e.,
    # "v/code/logs/access.log")
    access_log_path: str = os.path.join(logs_dir, "access.log")
    #
    # Create the full path to the error.log file
    error_log_path: str = os.path.join(logs_dir, "error.log")
    #
    # Check which log the user is requesting for
    if log_type == "access":
        #
        # Open the log file in read mode ("r")
        # "with" ensures the file is properly closed after reading
        with open(access_log_path, "r") as f:
            #
            # Read all lines from the file into a list
            lines = f.readlines()
            #
            # Get only the last 200 lines using negative indexing
            # [-200:] means "from 200 lines before the end to the end"
            last_200_lines = lines[-200:]
        #
        # Join all the lines back into a single string
        # "".join() combines list items with no separator (they already have \n)
        return "".join(last_200_lines)
    elif log_type == "error":
        #
        # Open the log file in read mode ("r")
        # "with" ensures the file is properly closed after reading
        with open(error_log_path, "r") as f:
            #
            # Read all lines from the file into a list
            lines = f.readlines()
            #
            # Get only the last 200 lines using negative indexing
            # [-200:] means "from 200 lines before the end to the end"
            last_200_lines = lines[-200:]
        #
        # Join all the lines back into a single string
        # "".join() combines list items with no separator (they already have \n)
        return "".join(last_200_lines)
    else:
        return "No log with such name"
