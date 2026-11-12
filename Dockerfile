FROM python:3.11-slim
WORKDIR /app
COPY ./app /app
RUN apt-get update && apt-get install -y git \
    && pip install --upgrade pip \
    && pip3 install --no-cache-dir -r requirements.txt
ENTRYPOINT ["python3" , "main.py"]