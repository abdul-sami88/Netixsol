# Production Sandbox Container for Judge0 / MicroVM Code Isolation
# Enforces unprivileged execution, read-only rootfs, and strict cgroups limits
FROM python:3.11-slim-bullseye

# Create unprivileged sandbox user
RUN groupadd -g 2000 sandboxgroup && \
    useradd -u 2000 -g sandboxgroup -m -s /bin/sh sandboxuser

# Harden filesystem permissions
RUN chmod 700 /home/sandboxuser && \
    mkdir -p /sandbox && \
    chown sandboxuser:sandboxgroup /sandbox && \
    chmod 750 /sandbox

# Disable network access entirely at container runtime via --network none
# Strip setuid / setgid binaries to prevent privilege escalation
RUN find / -perm /6000 -type f -exec chmod a-s {} \; || true

# Run as unprivileged student user
USER sandboxuser
WORKDIR /sandbox

# Environment constraints: No sensitive system paths, UTF-8 default
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    PATH="/usr/local/bin:/usr/bin:/bin"

# Resource limits enforced via docker run / cgroups v2:
# docker run --rm \
#   --network none \
#   --cpus 1.0 \
#   --memory 256m \
#   --memory-swap 256m \
#   --pids-limit 64 \
#   --read-only \
#   --tmpfs /tmp:rw,noexec,nosuid,size=32m \
#   --tmpfs /sandbox:rw,exec,nosuid,size=64m \
#   sandbox-runner python3 -I submission.py

ENTRYPOINT ["python3", "-I"]
CMD ["submission.py"]
