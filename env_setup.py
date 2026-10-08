import pathlib
import docker


BASE_IMG_TAG = "hobbyhacker-base:latest"
ROOT = pathlib.Path(__file__).parent


def build_base(client, force=False):
    try:
        if not force:
            client.images.get(BASE_IMG_TAG)
            print(f"[+] Base Image {BASE_IMG_TAG} already exists. Skipping the build....")
            return BASE_IMG_TAG
    except docker.errors.ImageNotFound:
        pass
    
    print(f"[+] Building {BASE_IMG_TAG} from Dockerfile...")
    image, logs = client.images.build(
            path=str(ROOT),
            tag=BASE_IMG_TAG,
            rm=True,
        )
        
    for chunks in logs:
            if "stream" in chunks:
                print(chunks["stream"],end="")
        
    print(f"[+] Built {BASE_IMG_TAG}")
    return BASE_IMG_TAG

def start_env(client, image=BASE_IMG_TAG, memory_limit="2g", cpu_limit=2.0):
    container = client.containers.run(
        image,
        detach=True,
        remove=False,
        cap_add=["NET_RAW", "NET_ADMIN"],
        mem_limit=memory_limit,
        nano_cpus=int(cpu_limit * 1e9),
        extra_hosts={"host.docker.internal": "host-gateway"},
        network="bridge",
    )
    print(f"[+] Sandbox Started : {container.short_id}")
    return container

def exec_in_env(container, command):
    result = container.exec_run(["bash", "-lc", command], demux=False)
    return result.exit_code, result.output.decode(errors="replace")

def stop_env(container):
    try:
        container.remove(force=True)
        print(f"[+] Sandbox {container.short_id} removed.")
    except docker.errors.NotFound:
        pass
    

if __name__ == "__main__":
    client = docker.from_env()
    build_base(client)
    c = start_env(client)
    try:
        rc, out = exec_in_env(c, "curl --version | head -n 1")
        print(f"rc={rc}  output={out.strip()}")
    finally:
        stop_env(c)