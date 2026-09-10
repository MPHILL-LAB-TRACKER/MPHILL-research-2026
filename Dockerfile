FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 TED2_DB=/data/ted2.sqlite3
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home ted2 && mkdir /data && chown ted2:ted2 /data
COPY --chown=ted2:ted2 backend backend
COPY --chown=ted2:ted2 web web
COPY --chown=ted2:ted2 data data
COPY --chown=ted2:ted2 manage.py .
USER ted2
VOLUME ["/data"]
EXPOSE 8000
CMD ["python", "manage.py", "serve", "--host", "0.0.0.0", "--port", "8000"]
