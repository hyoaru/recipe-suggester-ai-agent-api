# Build stage
FROM ghcr.io/astral-sh/uv:python3.12-alpine AS builder

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=0
WORKDIR /app

RUN \
  --mount=type=bind,source=.python-version,target=.python-version \
  --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
  --mount=type=bind,source=uv.lock,target=uv.lock \
  --mount=type=cache,target=/root/.cache/uv \
  uv sync --no-install-project --no-dev

COPY \
  .env \
  main.py \
  ./app \
  /app/

# Run stage
FROM python:3.12-alpine AS runner
WORKDIR /app

RUN apk add curl bash && apk cache clean \
  && addgroup -g 1000 nonroot \
  && adduser -u 1000 -G nonroot -S nonroot \
  && touch app.log \
  && chown 1000:1000 app.log

COPY --from=builder --chown=root:root --chmod=755 /app /app
USER nonroot

ENV PATH="/app/.venv/bin:$PATH"

CMD [ "fastapi", "run", "main.py", "--host", "0.0.0.0", "--port", "8000" ]
