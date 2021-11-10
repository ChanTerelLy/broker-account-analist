# Pull base image
FROM python:3.8

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /code
RUN mkdir -p /opt/data

# Install dependencies
RUN pip install pipenv
COPY Pipfile.lock /code/
COPY Pipfile /code/
RUN pipenv install --system --deploy --ignore-pipfile

# Copy project
COPY . /code/