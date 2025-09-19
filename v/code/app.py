#
# Import FastAPI to create endpoints for my app.
from fastapi import FastAPI
#
#
from fastapi.responses import HTMLResponse
from rentize import Client, Electricity

#
# Instantiate the FastAPI to a variable.
my_app = FastAPI()


#
# Home page to the app.
@my_app.get("/")
async def root():
    return {
        "message": "RENTIZE IS NOW ACCESSIBLE ON SERVER!"
    }

@my_app.get("/all_ebills", response_class=HTMLResponse)
def all_ebills():
    month = 8
    year = 2024
    client = Client(month, year)
    e_class = Electricity(client)
    df = e_class.get_all_bills()   # <-- this returns a DataFrame
    table_html = df.to_html(index=True)
    return f"""
    <html>
        <head><title>Electricity Bills</title></head>
        <body>
            <h2>Electricity Bills</h2>
            {table_html}
        </body>
    </html>
    """

