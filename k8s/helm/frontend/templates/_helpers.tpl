{{/* templates/_helpers.tpl */}}

{{/*
Expand the name of the chart.
*/}}
{{- define "frontend.name" -}}
{{- .Chart.Name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Full release name — Release.Name + Chart.Name, truncated to 63 chars (k8s limit).
*/}}
{{- define "frontend.fullname" -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels — applied to every resource so kubectl can filter them.
*/}}
{{- define "frontend.labels" -}}
app.kubernetes.io/name: {{ include "frontend.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/component: frontend
app.kubernetes.io/part-of: customer-sales-platform
{{- end }}

{{/*
Selector labels — used by Service and HPA to find the correct pods.
Must be a stable subset of labels — never change these after first deploy.
*/}}
{{- define "frontend.selectorLabels" -}}
app.kubernetes.io/name: {{ include "frontend.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
ConfigMap name — centralised so it's consistent across deployment and configmap templates.
*/}}
{{- define "frontend.configmapName" -}}
{{- printf "%s-config" (include "frontend.fullname" .) }}
{{- end }}