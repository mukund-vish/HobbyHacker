FROM ubuntu:22.04


ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        wget \
        git \
        vim \
        less \
        jq \
        unzip \
        ripgrep \
        file \
        net-tools \
        iproute2 \
        iputils-ping \
        dnsutils \
        python3 \
        python3-pip \
    && rm -rf /var/lib/apt/lists/*

CMD ["sleep", "infinity"]