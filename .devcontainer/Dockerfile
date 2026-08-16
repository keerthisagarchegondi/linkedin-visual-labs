FROM mcr.microsoft.com/devcontainers/python:3-3.13-bookworm

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ffmpeg \
        graphviz \
        libgl1 \
        libglib2.0-0 \
        libgomp1 \
        libsndfile1 \
        pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV DEBIAN_FRONTEND=