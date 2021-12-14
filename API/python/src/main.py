from typing import Optional
from fastapi import FastAPI, HTTPException, Body
import sys
from fastapi.responses import HTMLResponse
from processmodels.dewpoint import dewpointResults, dewpointCalc

app = FastAPI()

@app.get("/")
def read_root():
    html_content = """
    <html>
        <head>
            <title>NeqSim Python API</title>
        </head>        <body>
            <h1>NeqSim Python API</h1>
            <a href="/docs">NeqSimLive API documentation</a><br>
            <a href="https://github.com/EvenSol/NeqSim-Colab/tree/master/API/python">GitHub repo</a><br>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)

 
@app.post("/dewt",response_model=dewpointResults,description="Calculate the hydrocarbon dew point temperature")
def dewt(dewpoint:dewpointCalc):
    dewt2 = dewpoint.dewpointTemperature()
    if dewt2>500:
        raise HTTPException(
            status_code=400,
            detail="Hydrocarbon dew point temperature not found",
        )

    results = {
        'dewpointtemperature': float(dewt2)
    }
    return results