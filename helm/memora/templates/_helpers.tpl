{{/*
Expand the name of the chart.
*/}}
{{- define "memora.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "memora.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "memora.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "memora.labels" -}}
helm.sh/chart: {{ include "memora.chart" . }}
{{ include "memora.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "memora.selectorLabels" -}}
app.kubernetes.io/name: {{ include "memora.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
API labels
*/}}
{{- define "memora.api.labels" -}}
{{ include "memora.labels" . }}
app.kubernetes.io/component: api
{{- end }}

{{/*
API selector labels
*/}}
{{- define "memora.api.selectorLabels" -}}
{{ include "memora.selectorLabels" . }}
app.kubernetes.io/component: api
{{- end }}

{{/*
Control plane labels
*/}}
{{- define "memora.controlPlane.labels" -}}
{{ include "memora.labels" . }}
app.kubernetes.io/component: control-plane
{{- end }}

{{/*
Control plane selector labels
*/}}
{{- define "memora.controlPlane.selectorLabels" -}}
{{ include "memora.selectorLabels" . }}
app.kubernetes.io/component: control-plane
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "memora.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "memora.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Generate database URL
*/}}
{{- define "memora.databaseUrl" -}}
{{- if .Values.databaseUrl }}
{{- .Values.databaseUrl }}
{{- else if .Values.postgresql.enabled }}
{{- printf "postgresql://%s:%s@%s-postgresql:%d/%s" .Values.postgresql.auth.username .Values.postgresql.auth.password (include "memora.fullname" .) (.Values.postgresql.primary.service.port | int) .Values.postgresql.auth.database }}
{{- else }}
{{- printf "postgresql://%s:$(POSTGRES_PASSWORD)@%s:%d/%s" .Values.postgresql.external.username .Values.postgresql.external.host (.Values.postgresql.external.port | int) .Values.postgresql.external.database }}
{{- end }}
{{- end }}

{{/*
API URL for control plane
*/}}
{{- define "memora.apiUrl" -}}
{{- printf "http://%s-api:%d" (include "memora.fullname" .) (.Values.api.service.port | int) }}
{{- end }}
