FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends nftables curl ca-certificates iproute2 && rm -rf /var/lib/apt/lists/* && useradd -m agent
