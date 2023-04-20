FROM python:3.11.3-buster

WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install python dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# creating directories for the database and config files
RUN mkdir -p /app/volume

# copy project
COPY . .

# run run_script.sh
ENTRYPOINT ["/app/run_script.sh"]
