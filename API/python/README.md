# NeqSim Python API

This is a demonstration of how to make a NeqSim API in Python using packages:
* neqsim
* fastapi
* uvicorn

In the example a simple [hydrocarbon dew point calculation](https://github.com/EvenSol/NeqSim-Colab/blob/master/API/python/src/processmodels/dewpoint.py) is done, but in principle any neqsim calculation could be implemented.

A docker contaner soultion is developed, that the user can run as a cloud solution. See dockumentation for [FastAPI](https://fastapi.tiangolo.com/), [Uvicorn](https://www.uvicorn.org/) and [Docker](https://www.docker.com/) for how to set up and run the API.

The API can be run localy by using a local installation of Docker or via Python using the Uvicorn package.

Using Uvicorn:
run command (in src directory): 'uvicorn main:app --reload'

Using docker:
run command: 'docker compose up'

An example of using the API is given in [this notebook](https://github.com/EvenSol/NeqSim-Colab/blob/master/API/python/example/example.ipynb).

