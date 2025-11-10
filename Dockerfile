FROM python:3.11-slim

WORKDIR /app

# System deps for building wheels if needed
RUN apt-get update && apt-get install -y --no-install-recommends gcc build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home appuser
ENV PATH="/home/appuser/.local/bin:${PATH}"

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

USER appuser
ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "Src.main"]
