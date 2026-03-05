# Native validator: gRPC server; runs in-tree Python rules on deserialized scandata.
FROM python:3.12-slim

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir .

ENV APME_NATIVE_VALIDATOR_LISTEN=0.0.0.0:50055
EXPOSE 50055

CMD ["apme-native-validator"]
