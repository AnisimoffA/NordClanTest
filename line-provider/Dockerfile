FROM python:3.10.5

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD alembic upgrade head && gunicorn -k uvicorn.workers.UvicornWorker src.main:app --bind=0.0.0.0:8000 --log-level info