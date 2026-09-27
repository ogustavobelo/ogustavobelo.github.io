+++
date = '{{ .Date }}'
draft = true
title = '{{ replace .File.ContentBaseName "-" " " | title }}'
# Optional: a short description for meta/OG/JSON-LD previews. Falls back to
# the post's own summary when left unset.
# description = ''
# Optional: local page-bundle image(s) used as the OG/Twitter/JSON-LD image
# instead of the site default.
# images = ['photo.webp']
+++
