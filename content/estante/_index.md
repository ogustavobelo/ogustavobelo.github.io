+++
title = "Estante"
description = "Séries, filmes, livros, jogos e quadrinhos que estou acompanhando, terminei ou larguei pelo caminho."
outputs = ["HTML"]

# Each work is a page bundle with no page of its own: it only feeds the shelf
# grid (.Pages of this section) and stays out of .Site.RegularPages, so search,
# related posts, RSS, llms.txt and the sitemap never see it.
[[cascade]]
  [cascade.target]
    kind = "page"
  [cascade.build]
    render = "never"
    list = "local"
    publishResources = false
+++
