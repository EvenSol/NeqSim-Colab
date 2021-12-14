# NeqSim Python API

This is a demonstration of how to make a NeqSim API in Python using the packages:
neqsim
fastapi
uvicorn

In the example a simple hydrocarbon dew point calculation is done, but in principle any neqsim calculation could be implemented.

A docker contaner soultion is developed, that the user can run as a cloud solution. Leas see dockumentation for FastAPI, Uvicarn and docker for how to set up and run the API.

The API can be run localy by using docker or using Uvicorn (https://www.uvicorn.org/).

Using Uvicorn:
run command (in src directory): 'uvicorn main:app --reload'

Using docker:
run command: 'docker compose up'

An example of using the API is given in [this notebook](https://github.com/EvenSol/NeqSim-Colab/blob/master/API/python/example/example.ipynb).

