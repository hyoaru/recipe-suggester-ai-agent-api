FROM python:3.13-alpine

WORKDIR /app

COPY pyproject.toml uv.lock .python-version ./

RUN pip install --no-cache-dir uv
RUN uv install

COPY . .

CMD [ "uv", "run", "fastapi", "run", "main.py", "--host", "0.0.0.0", "--port", "8000" ]
