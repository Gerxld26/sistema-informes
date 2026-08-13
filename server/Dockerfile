FROM python:3.12-slim

WORKDIR /app

COPY server/requirements.txt server-requirements.txt
RUN pip install --no-cache-dir -r server-requirements.txt

COPY pyproject.toml pyproject.toml
COPY src src
RUN pip install --no-cache-dir -e .

COPY server server
COPY plantillas plantillas
COPY intake intake

ENV INFORMES_DB_PATH=/app/data/informes.db
ENV INFORMES_NAS_PATH=/app/nas_output

EXPOSE 8000

CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
