FROM postgres:16-alpine

# Copy schema and seed scripts to auto-initialize DB on startup
COPY init_scripts/ /docker-entrypoint-initdb.d/

EXPOSE 5432
