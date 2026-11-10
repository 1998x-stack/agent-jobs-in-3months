# Deployment & Infrastructure Placeholders

This directory exists for the P2 production upgrade. No cloud deployment is configured by default.

- `docker/`：容器、资源限额及开发服务（TODO）。
- `k8s/`：Deployment/Worker/HPA/NetworkPolicy（TODO）。
- `observability/`：OpenTelemetry collector、dashboard、SLO（TODO）。

Security reminder: a Dockerfile alone does not constitute a secure sandbox.
