FROM openjdk:8
COPY --from=tiangolo/uvicorn-gunicorn:latest / /
RUN java -version
RUN python --version

# set the working directory in the container
WORKDIR /code

COPY requirements.txt .

# install dependencies
RUN pip install -r requirements.txt

# copy the content of the local src directory to the working directory
COPY src/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]