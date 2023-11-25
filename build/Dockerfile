FROM ghcr.io/azuki774/selenium-chrome:0.2.0
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && pip install -r /tmp/requirements.txt

ENTRYPOINT ["python3", "-u", "/src/main.py"]
