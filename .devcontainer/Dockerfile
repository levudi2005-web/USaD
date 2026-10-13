FROM node:24-trixie

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        git \
        openjdk-21-jdk \
        python3 \
        python3-venv \
    && rm -rf /var/lib/apt/lists/* \
    && groupmod --new-name developer node \
    && usermod --login developer --home /home/developer --move-home node \
    && mkdir -p /workspace \
    && chown -R developer:developer /home/developer /workspace

USER developer
WORKDIR /workspace

CMD ["sleep", "infinity"]
