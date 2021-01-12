# First stage to export the dependencies from poetry
# to "classic" requirements.txt for pip to consume.
FROM python:3.8-slim as requirements_export

RUN pip install poetry

COPY pyproject.toml poetry.lock ./
RUN poetry export -o /requirements.txt


# Second stage for the actual build
FROM python:3.8-slim

WORKDIR /app
COPY tools/*.sh ./tools/
COPY --from=requirements_export /requirements.txt ./
RUN \
    chmod +x ./tools/* && \
    ./tools/dependencies-pre.sh && \
    pip install -r requirements.txt && \
    ./tools/dependencies-post.sh

COPY uptimer ./uptimer

ENV UPTIMER_ENV=production
ENV PYTHONUNBUFFERED=1

USER nobody:nogroup

ENTRYPOINT ["tini", "--"]
CMD ["python", "-m", "uptimer"]
