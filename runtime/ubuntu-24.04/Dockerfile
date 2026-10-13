FROM ubuntu:24.04

ARG NODE_VERSION=24.21.0
ARG TARGETARCH

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        composer \
        coreutils \
        curl \
        default-mysql-client \
        fd-find \
        file \
        findutils \
        g++ \
        gcc \
        gawk \
        gdb \
        git \
        golang-go \
        gzip \
        iproute2 \
        iputils-ping \
        jq \
        less \
        make \
        nano \
        openjdk-21-jdk-headless \
        passwd \
        php-bcmath \
        php-cli \
        php-curl \
        php-gd \
        php-intl \
        php-mbstring \
        php-mysql \
        php-pgsql \
        php-sqlite3 \
        php-xml \
        php-zip \
        postgresql-client \
        procps \
        python3 \
        python3-pip \
        python3-venv \
        ripgrep \
        ruby \
        ruby-dev \
        ruby-rubygems \
        rustc \
        cargo \
        sed \
        sqlite3 \
        tar \
        tmux \
        tree \
        unzip \
        vim-tiny \
        wget \
        xz-utils \
        zip \
        xxd; \
    ln -sf /usr/bin/vim.tiny /usr/local/bin/vim; \
    ln -sf /usr/bin/fdfind /usr/local/bin/fd; \
    case "${TARGETARCH:-amd64}" in \
        amd64) node_arch=x64 ;; \
        arm64) node_arch=arm64 ;; \
        *) echo "Unsupported target architecture: ${TARGETARCH}" >&2; exit 1 ;; \
    esac; \
    archive="node-v${NODE_VERSION}-linux-${node_arch}.tar.xz"; \
    mkdir -p /tmp/node-download /opt/node; \
    cd /tmp/node-download; \
    curl -fsSLO "https://nodejs.org/dist/v${NODE_VERSION}/${archive}"; \
    curl -fsSLO "https://nodejs.org/dist/v${NODE_VERSION}/SHASUMS256.txt"; \
    checksum="$(awk -v name="${archive}" '$2 == name { print $1 }' SHASUMS256.txt)"; \
    test -n "${checksum}"; \
    printf '%s  %s\n' "${checksum}" "${archive}" | sha256sum --check --strict -; \
    tar -xJf "${archive}" --strip-components=1 -C /opt/node; \
    ln -s /opt/node/bin/node /usr/local/bin/node; \
    ln -s /opt/node/bin/npm /usr/local/bin/npm; \
    ln -s /opt/node/bin/npx /usr/local/bin/npx; \
    cd /; \
    apt-get clean; \
    rm -rf /tmp/node-download /var/lib/apt/lists/*

RUN set -eux; \
    useradd --uid 10001 --create-home --shell /bin/bash developer; \
    install -d -o developer -g developer /workspace

ENV HOME=/home/developer
WORKDIR /workspace
USER developer

CMD ["/bin/bash"]
