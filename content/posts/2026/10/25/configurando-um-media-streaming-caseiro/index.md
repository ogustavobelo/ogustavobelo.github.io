+++
title = "Configurando um media streaming caseiro"
date = "2026-10-25T17:25:49-03:00"
draft = false
tags = ["tech", "open-source"]
description = "Como configurei um servidor local onde baixo e assisto séries e filmes"
+++

{{< image src="image.png" alt="image" class="image-frame" >}}

Esse fim de semana gastei algumas horinhas, e muitos tokens, para iniciar um projeto que tanto planejo: meu Home Lab. 
Já venho usando o Jellyfin há algum tempo mas o processo estava inteiramente manual, até que um amigo (Valeu, Jovane <3) compartilhou o [seguinte tutorial](https://bishalkshah.com.np/blog/ultimate-2026-media-stack-jellyfin-arrs).

A ideia foi configurar Sonarr + Radarr + Bazarr + Prowlarr + Seer + Jellyfin, com isso você consegue listar todas as mídias disponíveis (filmes e séries), baixando e disponibilizando para a TV AUTOMAGICAMENTE.

Depois do básico adicionado, adicionei um *temperinho* a mais onde consigo acessar obras dubladas (confesso que animação é algo que eu prefiro assistir dublado) e conecto a legenda.
Atualmente, deixei tudo rodando no meu Mac pessoal mas acho num futuro próximo vou levar todo esta configuração para um desktop Linux. Pensando nisso, já aproveitei e criei um repo privado com tudo que já deixei pronto a um script de distância.

Já inspirado em [outro artigo](https://viceconsole.fyi/blog/2026/10/10/what-i-self-host/), enxergo deixando este desktop como um servidor local que será incrementado com outras *cositas más*:
- Streaming multimídia para redes externas
- Instância local do Bitwarden
- Central de arquivos compartilhados
- Assistente da casa