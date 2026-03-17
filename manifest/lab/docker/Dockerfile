FROM python:3.11-slim

WORKDIR /app

RUN pip install flask redis

COPY hello.py .

ENV REDIS_HOST=redis
EXPOSE 5000

CMD ["python", "hello.py"]