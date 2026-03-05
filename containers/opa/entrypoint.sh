#!/usr/bin/env bash
# Start OPA REST server in the background, then run the gRPC wrapper.
set -e

opa run --server --addr=0.0.0.0:8181 /bundle &
OPA_PID=$!

# Wait for OPA to be ready
for i in $(seq 1 30); do
    if curl -sf http://localhost:8181/health >/dev/null 2>&1; then
        break
    fi
    sleep 0.5
done

exec apme-opa-validator
