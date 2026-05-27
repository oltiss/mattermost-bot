FROM python:3.12-slim

WORKDIR /app

<<<<<<< HEAD
RUN pip install poetry==1.8.3

COPY pyproject.toml poetry.lock ./

RUN poetry install --only main --no-root

COPY . .

CMD ["poetry", "run", "gunicorn", "--bind", "0.0.0.0:5000", "mattermost:app"]
=======
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "mattermost:app"]
>>>>>>> origin/main
