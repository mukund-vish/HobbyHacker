import docker

client = docker.from_env()

IMAGE = "ubuntu:22.04"
client.images.pull(IMAGE)
print(f"Pulled {IMAGE}\n")

script = r"""
set -e
export DEBIAN_FRONTEND=noninteractive

# ---- Install tools (silent) ----
apt-get update -qq
apt-get install -y -qq --no-install-recommends \
    ca-certificates curl wget git vim less jq unzip \
    net-tools iproute2 iputils-ping dnsutils whois traceroute \
    netcat-openbsd socat telnet tcpdump \
    nmap \
    openssh-client \
    python3 python3-pip \
    >/dev/null 2>&1

echo "=== Tools ready, starting work ===\n"

# ---- Pentest commands ----
nmap --version | head -n 1
echo
echo "--- DNS lookup ---"
getent hosts example.com || true
echo
echo "--- HTTP headers ---"
curl -sI https://example.com | head -n 5
echo
echo "--- Python check ---"
python3 -c "import socket; print('local ip:', socket.gethostbyname(socket.gethostname()))"
"""

output = client.containers.run(
    IMAGE,
    ["bash", "-c", script],
    remove=True,                      
    cap_add=["NET_RAW", "NET_ADMIN"], 
)

print(output.decode())
print("Container removed.")