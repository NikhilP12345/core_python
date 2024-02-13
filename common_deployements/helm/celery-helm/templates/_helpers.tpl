{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "celery-helm.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}


{{/*
Common labels
*/}}
{{- define "celery-helm.labels" -}}
helm.sh/chart: {{ include "celery-helm.chart" . }}
{{ include "celery-helm.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}


{{/*
Selector labels
*/}}
{{- define "celery-helm.selectorLabels" -}}
app.kubernetes.io/name: {{ include "celery-helm.serviceAccountName" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}


{{/*
Create the name of the service account to use
*/}}
{{- define "celery-helm.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- printf "%s-%s-%s" .Release.Name .Values.k8sNamespace .Values.deploymentEnv }}
{{- else }}
default
{{- end }}
{{- end }}


{{/*
Build full image name
*/}}
{{- define "celery-helm.fullImageName" }}
{{- printf "%s:%s" .Values.image.repository .Values.image.tag }}
{{- end }}


{{/*
Pass shared environment variables from map
*/}}
{{- define "celery-helm.sharedEnvList" }}
            - name: APP_ENV
              value: {{ .Values.deploymentEnv }}
{{- range $env_name, $env_value := .Values.sharedEnv }}
            - name: {{ $env_name }}
              value: {{ $env_value }}
{{- end }}
{{- end }}
