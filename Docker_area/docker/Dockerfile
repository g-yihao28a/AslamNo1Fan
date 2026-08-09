FROM apache/superset:latest

USER root
COPY requirements-local.txt /app/docker/requirements-local.txt
RUN uv pip install --python /app/.venv/bin/python --no-cache -r /app/docker/requirements-local.txt
USER superset