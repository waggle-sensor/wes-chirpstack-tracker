FROM python:3.8-slim
WORKDIR /app
COPY ./app /app
RUN pip install --upgrade pip \
    && pip3 install --no-cache-dir -r requirements.txt
ENTRYPOINT ["python3" , "main.py"]