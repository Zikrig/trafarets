FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN mkdir -p data pdfs

VOLUME /app/data
VOLUME /app/pdfs

CMD ["python", "bot.py"]