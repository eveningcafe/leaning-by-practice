FROM python:3.11-slim
WORKDIR /app
RUN pip install flask
COPY . .
RUN mkdir -p /app/db
CMD ["python", "app.py"]
