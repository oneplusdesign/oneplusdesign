# AΩ research-only worker. Run with AO-AI/compose.yaml on an approved host.
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONPATH=/app/research \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    AO_STATE_DIR=/state
COPY research/ /app/research/
RUN mkdir -p /state && chown 65532:65532 /state \
    && python -m unittest discover -s /app/research -p 'test_*.py' -q
USER 65532:65532
HEALTHCHECK --interval=90s --timeout=15s --start-period=5m --retries=3 \
  CMD python -m always_on_worker --healthcheck --state-dir /state || exit 1
ENTRYPOINT ["python","-m","always_on_worker"]
