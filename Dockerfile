FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN python -m pip install --upgrade pip
RUN python -m pip install -r requirements.txt

CMD ["python", "-m", "streamlit", "run", "demo/Homepage.py", "--logger.level=debug", "--server.port=8080"]

EXPOSE 8080
