# Ansible validator: gRPC server; runs Ansible syntax/argspec using shared cache.
# Mount cache volume at /cache (read-only).
# Pre-built venvs with ansible-core 2.18, 2.19, 2.20 at /opt/ansible-venvs/<version>.
FROM python:3.12-slim

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir .

# Pre-build ansible-core venvs (no network needed at runtime for supported versions)
RUN chmod +x containers/ansible/prebuild-venvs.sh \
    && containers/ansible/prebuild-venvs.sh /opt/ansible-venvs

ENV APME_ANSIBLE_VALIDATOR_LISTEN=0.0.0.0:50053
ENV APME_CACHE_ROOT=/cache
ENV APME_ANSIBLE_VENVS_ROOT=/opt/ansible-venvs
EXPOSE 50053

CMD ["apme-ansible-validator"]
