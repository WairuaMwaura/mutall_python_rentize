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
# Import datetime to select date values.
from datetime import datetime
import calendar
#
# Instantiate the FastAPI to a variable.
my_app = FastAPI()
# 
# Mount a folder for static files. 
# Anytime someone visits /static/... in the browser, serve them files from this folder.
# It creates an actual route (/static) in the app.
my_app.mount("/static", StaticFiles(directory="../static"), name="static")
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
    ebills_table = ebills_df.to_html(index=False)
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
    client_ebills_table = client_ebills_df.to_html(index=False)
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
    ebills_table = ebills_df.to_html(index=False)
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
    client_ebills_table = client_ebills_df.to_html(index=False)
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
    unattended_ebills_table = unattended_ebills_df.to_html(index=False)
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
    service_ebills_table = service_ebills_df.to_html(index=False)
    #
    # Define the structure of the HTML to be sent to the template.
    html_content = f"""
        <h2>Service Electricity Bills for {calendar.month_name[month]} {year}</h2>
        <h3>Total entries {num_rows}</h3>
        {service_ebills_table}
    """

    return HTMLResponse(content=html_content)

#
# Sample page showing dynamic content loading.
@my_app.get("/reactive", response_class=HTMLResponse)
def reactive_page(request: Request):
    """Serves the reactive UI page"""
    return templates.TemplateResponse(
        "reactive_ui.html",
        {
            "request": request
        }
    )

# Your existing /process endpoint is good!
@my_app.post("/process", response_class=HTMLResponse)
async def process_input(request: Request) -> HTMLResponse:
    """
    Receives JSON from the frontend and returns HTML content.
    """
    # Read incoming JSON data from the request body
    data: dict = await request.json()

    # Extract the "input" value safely
    user_input: str = data.get("input", "")

    # Simulate processing (replace with your logic)
    result_html: str = f"<p>You typed <b>{user_input}</b>: Here it is in uppercase <b>{user_input.upper()}</b></p>"

    # Return the processed result as plain HTML
    return HTMLResponse(content=result_html)