+++
title = "Catalogando mais de 10 anos de mídias"
date = "2026-09-30T20:30:36-03:00"
draft = false
tags = ["open-source", "tech", "arthur"]
description = "Utilizando de ferramentas open-source para catalogar as mídias exportadas do instagram"
+++

Eu uso instagram desde 2013. Passei por (literalmente) uma dezena de empregos. Iniciei 3 cursos de graduação e 1 pós. Comecei a namorar, casei, tive um filho, ensinei ele a jogar Capcom vs Marvel e perdi para ele alguns meses depois. Li uma centena de livros, assisti centenas de filmes, fui comer em restaurantes em vários estados, tomei várias cachaças, palestrei algumas vezes. Tudo isso foi compartilhado no instagram: seja nas postagens ou nos stories. Mais de 13 anos da minha vida compartilhados em vídeos e imagens em um servidor aleatório no Vale do Silício.

Recentemente, desativei o instagram. No segundo dia, eu senti falta de ver uns vídeos do Arthur que eu tinha armazenado nos destaques do meu perfil e eu não tinha salvo em nenhum outro lugar.  Já pensou? Perder mais de dez anos de registros da minha vida. Acho que quando você usa essas plataformas de terceiros fica com um sentimento que eles tão cuidando deste armazenamento pra você. Só que até quando? 

Felizmente, é possível você exportar todas as mídias que você armazenou durante todo o uso de maneira simplificada. Segue as [instruções do próprio instagram](https://help.instagram.com/181231772500920/).

Então, rapidamente reativei a conta e solicitei que eles me enviassem tudo. No mesmo dia, recebi um e-mail contendo um link para o download de um zip que continha tudo. Tudo mesmo, até as preferências de uso, pesquisas, mensagens, informações pessoas, etc.

{{< image src="instagram-export-tree.png" alt="instagram-export-tree" class="image-frame" >}}

Tá... Agora com literalmente milhares de arquivos. Alguns deles de um fundo colorido com texto em letras garrafais xingando algum político aleatório. Ou um boomerang de uma dose de cachaça sendo despejada na boca de um amigo. Ou o print de uma notícia (antes não existia o compartilhar no instagram)... e assim, vai. Como separar as mídias que realmente me interessam? Com algumas pesquisas rápidas descobri o [DigiKam](https://www.digikam.org/documentation/), software open-source com ferramentas para gestão de imagens.

Entre as várias funções disponíveis temos uma toolkit de reconhecimento facial que me permitiu com pouquíssimas configurações filtrar e taguear as que apareciam eu, a Marília e/ou o Arthur.
Além de criar esses álbuns, ele altera os metadados da imagem adicionando as tags identificadas.

{{< image src="gustavo-belo-face-recognition.png" alt="imgustavo-belo-face-recognitionage" class="image-frame" >}}

Isso já resolveu parte do problema, consegui separar e catalogar as imagens que mais me interessavam e deletar as que foram apenas postagens frívolas. Só que ainda tinham milhares de vídeos que o DigiKam não consegue catalogar.

A saída foi aproveitar o trabalho de tagueamento que eu já tinha havia feito anteriormente e escrever um scriptzinho para mesclar a análise com outras tecnologias. Li o banco digikam4.db com sqlite3, peguei só as fotos com uma única pessoa tagueada e o [insightface](https://pypi.org/project/insightface/) (modelo buffalo_l) transformou cada rosto em um vetor numérico. Ele roda sobre o onnxruntime, direto na CPU do Mac, sem mandar nada para a nuvem. Depois, com o opencv abriu cada vídeo e pegou um frame por segundo, até 30 por vídeo. Cada rosto detectado foi comparado com as referências por similaridade de cosseno, e o resultado virou três faixas: "certo", "duvidoso" e "sem correspondência". 

 Para quem nunca programou, pode soar como ciência de foguetes mas garanto que é algo relativamente simples, com poucas linhas de comando que podem ser cuspidas por qualquer LLM:
 
 {{< image src="scan-videos-code.png" alt="scan-videos-code" class="image-frame" >}}


Como o Arthur muda muito de aparência com a idade, comparei cada rosto com todas as referências de cada pessoa e fiquei com a mais parecida, em vez de usar uma média. Por fim, para a catalogação não se perder, usei ffmpeg para copiar os streams sem recodificar e gravar os nomes nos metadados. O exiftool acrescentou as tags People/Nome do digiKam. Então, um filtro futuro por nome acha tudo sem refazer a varredura. Com uma breve análise manual, basicamente pela thumb e minha memória sobre o contexto, movi entre as pastas e voilá

{{< image src="videos-catalog.png" alt="videos-catalog" class="image-frame" >}}

Agora tenho todas as fotos e vídeos que eu queria organizadas e catalogadas, seja por data do registro, como pelas pessoas que aparecessem.





