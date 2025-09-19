#
# Import FastAPI to create endpoints for my app.
from fastapi import FastAPI
# 
# 
from fastapi.staticfiles import StaticFiles
#
#
from fastapi.responses import HTMLResponse
# 
# Import my classes
from rentize import Client, Electricity

#
# Instantiate the FastAPI to a variable.
my_app = FastAPI()
# 
# Mount a folder for static files.
my_app.mount("/static", StaticFiles(directory="static"), name="static")
#
# Home page to the app.
@my_app.get("/")
async def root():
    return {
        "message": "RENTIZE IS NOW ACCESSIBLE ON SERVER!"
    }

@my_app.get("/all_ebills", response_class=HTMLResponse)
def all_ebills():
    month = 9
    year = 2024
    client = Client(month, year)
    e_class = Electricity(client)
    df = e_class.get_all_bills()
    table_html = df.to_html(index=True)
    return f"""
    <html>
        <head><title>Electricity Bills</title></head>
        <link rel="stylesheet" href="/static/table.css">
        <body>
            <h2>Electricity Bills</h2>
            {table_html}
            <script src="/static/table.js"></script> 
        </body>
    </html>
    """

