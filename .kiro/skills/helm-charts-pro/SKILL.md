---
name: helm-charts-pro
description: "Helm chart creation, management, and best practices for Kubernetes deployments. Use for packaging, templating, and releasing Kubernetes applications with Helm 3."
user-invocable: true
risk: safe
---

# Helm Charts Pro

Expert Helm chart developer — create, template, test, and publish production-grade Helm charts.

## When to Use
- Creating a new Helm chart for a Kubernetes application
- Templating complex Kubernetes manifests with values
- Managing chart dependencies and subcharts
- Publishing charts to a Helm repository
- Implementing Helm hooks for lifecycle management

## Chart Structure
```
mychart/
├── Chart.yaml          # Chart metadata
├── values.yaml         # Default values
├── values.schema.json  # Values validation (recommended)
├── templates/
│   ├── _helpers.tpl    # Named templates
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── configmap.yaml
│   ├── hpa.yaml
│   └── NOTES.txt       # Post-install instructions
└── charts/             # Subcharts
```

## Chart.yaml
```yaml
apiVersion: v2
name: myapp
description: My application Helm chart
type: application
version: 1.2.3         # Chart version (semver)
appVersion: "2.0.0"    # App version (informational)
dependencies:
  - name: postgresql
    version: "13.x.x"
    repository: https://charts.bitnami.com/bitnami
    condition: postgresql.enabled
```

## Deployment Template
```yaml
# templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "mychart.fullname" . }}
  labels:
    {{- include "mychart.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "mychart.selectorLabels" . | nindent 6 }}
  template:
    spec:
      containers:
        - name: {{ .Chart.Name }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
          ports:
            - containerPort: {{ .Values.service.port }}
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
          {{- with .Values.env }}
          env:
            {{- toYaml . | nindent 12 }}
          {{- end }}
```

## values.yaml Best Practices
```yaml
replicaCount: 1

image:
  repository: myregistry/myapp
  pullPolicy: IfNotPresent
  tag: ""  # Defaults to Chart.AppVersion

service:
  type: ClusterIP
  port: 80

ingress:
  enabled: false
  className: nginx
  hosts: []

resources:
  limits:
    cpu: 500m
    memory: 128Mi
  requests:
    cpu: 100m
    memory: 64Mi

autoscaling:
  enabled: false
  minReplicas: 1
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80
```

## Helm Hooks
```yaml
# Pre-install database migration job
annotations:
  "helm.sh/hook": pre-install,pre-upgrade
  "helm.sh/hook-weight": "-1"
  "helm.sh/hook-delete-policy": hook-succeeded
```

## Testing & Linting
```bash
helm lint ./mychart
helm template mychart ./mychart --debug
helm test myrelease
ct lint --charts ./charts  # chart-testing
```

## Common Commands
```bash
helm install myapp ./mychart -f custom-values.yaml
helm upgrade myapp ./mychart --set image.tag=v2.0.0
helm rollback myapp 1
helm history myapp
helm get values myapp
```

## Best Practices
- Always define `resources` limits and requests
- Use `_helpers.tpl` for reusable named templates
- Validate values with `values.schema.json`
- Never hardcode secrets — use `secretKeyRef` or external-secrets
- Use `helm.sh/hook-delete-policy: before-hook-creation,hook-succeeded` for clean hooks
