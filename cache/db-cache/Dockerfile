FROM python:3.11-slim
WORKDIR /app
RUN pip install flask redis pymysql
COPY app.py .
CMD ["python", "app.py"]
