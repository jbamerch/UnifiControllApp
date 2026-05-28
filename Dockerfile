FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

ENV FLASK_APP=src/app.py
ENV FLASK_ENV=production

EXPOSE 5000

CMD ["python", "src/app.py"]
