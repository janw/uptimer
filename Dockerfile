# First stage to export the dependencies from poetry
# to "classic" requirements.txt for pip to consume.
FROM python:3.8 as requirements_export

RUN pip install poetry

WORKDIR /tmp
COPY pyproject.toml poetry.lock ./
RUN poetry export -o /requirements.txt

RUN wget -qO /usr/bin/dbmate \
    https://github.com/amacneil/dbmate/releases/latest/download/dbmate-linux-amd64 && \
    chmod +x /usr/bin/dbmate

# Second stage for the actual build
FROM python:3.8-slim

WORKDIR /app
COPY tools/dependencies*.sh ./tools/
COPY --from=requirements_export /usr/bin/dbmate /usr/bin/dbmate
COPY --from=requirements_export /requirements.txt ./
RUN \
    chmod +x ./tools/* && \
    ./tools/dependencies-pre.sh && \
    pip install --no-cache-dir -r requirements.txt && \
    ./tools/dependencies-post.sh

COPY tools/entrypoint.sh /
COPY uptimer ./uptimer
COPY db ./db

ENV UPTIMER_ENV=production
ENV PYTHONUNBUFFERED=1

USER nobody:nogroup

ENTRYPOINT ["tini", "--"]
CMD ["/entrypoint.sh"]
