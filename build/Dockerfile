FROM python:3.11-slim-buster
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && pip install -r /tmp/requirements.txt
COPY src /src

ENTRYPOINT ["python3", "-u", "/src/main.py"]
