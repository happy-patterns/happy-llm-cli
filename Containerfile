# Use a specific Fedora base image for consistency
FROM fedora:41

# Set labels
LABEL maintainer="Happy Patterns <jeffrey@happy-patterns.com" \
  description="Development environment for Happy Patterns LLM CLI tool"

# System dependencies
RUN dnf update -y && \
  dnf install -y \
  python3 python3-pip python3-devel git \
  && dnf clean all

# Setup non-root user
ARG USERNAME=devuser
ARG USER_UID=1000
ARG USER_GID=${USER_UID}
RUN groupadd --gid ${USER_GID} ${USERNAME} && \
  useradd --uid ${USER_UID} --gid ${USER_GID} -m ${USERNAME}

USER ${USERNAME}
WORKDIR /home/${USERNAME}/app

# Python environment setup
COPY --chown=${USERNAME}:${USERNAME} requirements.txt .
RUN python3 -m venv .venv
ENV PATH="/home/${USERNAME}/app/.venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=${USERNAME}:${USERNAME} . .
