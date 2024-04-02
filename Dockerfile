FROM python:3.12-slim AS base

RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources
RUN sed -i 's/security.debian.com/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl wget gcc g++ protobuf-compiler libpq-dev && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1
ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN pip config set global.index-url http://mirrors.aliyun.com/pypi/simple
RUN pip config set install.trusted-host mirrors.aliyun.com
RUN pip install -U pip wheel poetry==1.6.1
RUN poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-dev --no-interaction --no-ansi

COPY . .

ENTRYPOINT ["python"]
CMD ["-m", "internal.grpc.main"]
