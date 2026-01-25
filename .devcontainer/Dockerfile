FROM python:3.12.12

ARG REMOTE_USER
ARG REMOTE_UID
ARG REMOTE_GID

# Install dependencies
RUN apt-get update && apt-get install -y \
    bash-completion \
    && apt-get clean

# Enable bash completion
RUN echo "source /etc/bash_completion" >> ~/.bashrc

# Create a non-root user matching the current host user
RUN groupadd --gid $REMOTE_GID $REMOTE_USER \
    && useradd --uid $REMOTE_UID --gid $REMOTE_GID -m $REMOTE_USER \
    && apt-get install -y sudo \
    && echo $REMOTE_USER ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$REMOTE_USER \
    && chmod 0440 /etc/sudoers.d/$REMOTE_USER

# Add /home/$REMOTE_USER/.local/bin to PATH
ENV PATH="/home/$REMOTE_USER/.local/bin:${PATH}"

# Switch to the non-root user
USER $REMOTE_USER

# Install uv package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
