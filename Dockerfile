FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PETSUS_DATABASE_FILE=/app/data/usuarios.db \
    PETSUS_DATA_FILE=/app/dados_dashboard_saude.xlsx

WORKDIR /app

RUN groupadd --gid 10001 petsus \
    && useradd --uid 10001 --gid petsus --no-create-home --home-dir /app --shell /usr/sbin/nologin petsus

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY --chown=petsus:petsus . .
RUN mkdir -p /app/data \
    && chown -R petsus:petsus /app/data

USER petsus

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=3)" || exit 1

CMD ["python", "-m", "streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
