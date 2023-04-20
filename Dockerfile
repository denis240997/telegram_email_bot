FROM python:3.11.3-buster

WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install python dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

RUN mkdir -p /app/volume
COPY . .

# run entrypoint.sh
ENTRYPOINT ["/app/run_script.sh"]
# ENTRYPOINT ["/bin/bash"]