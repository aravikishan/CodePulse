FROM python:3.11-slim

LABEL maintainer="ravikishan" \
      description="CodePulse - Python Code Analysis Tool"

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p instance uploads

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

RUN chmod +x start.sh 2>/dev/null || true

CMD ["bash", "start.sh"]
