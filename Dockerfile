FROM python:3.12-slim

WORKDIR /app

RUN pip install poetry==1.8.3

COPY pyproject.toml poetry.lock ./

RUN poetry install --only main --no-root

COPY . .

CMD ["poetry", "run", "gunicorn", "--bind", "0.0.0.0:5000", "mattermost:app"]
