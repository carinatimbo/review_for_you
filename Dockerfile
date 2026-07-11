# Deploy do projeto (ingestor + dashboard) na VPS via Coolify. Adicionado pelo professor.
# Layout raiz: scheduler.py + app.py + ingestor/. Não altera o código de vocês.
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements.txt .
# streamlit não está no requirements.txt, mas o app.py precisa dele — instalado aqui.
RUN pip install --upgrade pip && pip install -r requirements.txt && pip install streamlit
COPY . .
RUN mkdir -p /app/datalake
EXPOSE 8501
