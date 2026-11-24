# Imagen de la API de Data Health Platform (FastAPI)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Primero las dependencias (capa que se reutiliza si no cambian)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Luego el código y los datos de demostración
COPY app ./app
COPY sample_data ./sample_data

# Usuario sin privilegios
RUN useradd --create-home dhp
USER dhp

EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health', timeout=4)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
