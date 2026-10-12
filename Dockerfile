FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt requirements-production.txt ./
RUN pip install --no-cache-dir -r requirements-production.txt \
    && groupadd --gid 10001 repair \
    && useradd --uid 10001 --gid repair --no-create-home repair \
    && mkdir /app/instance \
    && chown repair:repair /app/instance
COPY --chown=repair:repair app.py models.py services.py index.html ./
COPY --chown=repair:repair templates/ templates/
COPY --chown=repair:repair static/ static/
COPY --chown=repair:repair tests/ tests/
COPY --chown=repair:repair deploy/entrypoint.sh /app/entrypoint.sh
USER repair
EXPOSE 8000
ENTRYPOINT ["sh", "/app/entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "4", "--timeout", "60", "--access-logfile", "-", "--error-logfile", "-", "app:create_app()"]
