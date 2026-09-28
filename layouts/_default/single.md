{{- if not (.Scratch.Get "params") -}}
    {{- partial "init.html" . -}}
{{- end -}}
# {{ .Title }}

> {{ partial "function/description.html" . }}

Fonte: {{ .Permalink }}
{{- with .Date }}
Publicado em: {{ .Format "2006-01-02" }}
{{- end }}

{{ partial "function/markdown.html" . }}
