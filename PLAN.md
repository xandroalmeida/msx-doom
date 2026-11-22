# Posto Umbra para MSX1 com 64 KiB

A campanha original está jogável do título ao final. Ela preserva exploração em primeira pessoa, mira, combate, controle de munição e uso de chaves em um cartucho de 16 KiB.

## Plataforma e orçamento

| Recurso | Implementação |
| --- | --- |
| CPU | Z80 a aproximadamente 3,58 MHz. Coordenadas de ponto fixo 8.8 e tabelas geradas no build. |
| Vídeo | VDP da classe TMS9918 com 16 KiB de VRAM. SCREEN 2 a 256 × 192, com janela 3D de 256 × 128. |
| RAM | MSX1 de 64 KiB. Os buffers e estados explícitos do cartucho cabem em `C000h–C3FFh`. O BIOS mantém sua pilha e área de trabalho nas regiões habituais. |
| ROM | Cartucho linear em `4000h–7FFFh`. O binário ocupa 14.437 bytes, incluindo alinhamento, e deixa 1.947 bytes na imagem de 16 KiB. |
| Geometria | Três mapas de 16 × 16 células e paredes ortogonais de altura uniforme. O mapa atual é expandido em RAM para permitir abrir a porta. |
| Renderização | 32 raios por quadro e 64 direções de câmera. A ROM guarda os vetores de um quadrante e o Z80 gira os demais. Nas transições de face ou material, a coluna de pedra mais próxima recebe um chanfro. A projeção por tiles reutiliza a profundidade das paredes e ordena os objetos de trás para frente. |
| Som | PSG integrado. O tema original da abertura usa três canais de tom e ruído. Durante a campanha, a arma usa ruído no canal A, interações e saída usam o canal B, e o impacto ao sofrer dano usa o canal C. |

As duas tabelas de nomes ficam em `1800h` e `1C00h` na VRAM. O jogo envia 512 nomes de tiles e a linha do HUD à página oculta antes de apresentá-la no VBlank. Cinco corações mostram a vida restante. Os objetos usam quatro tamanhos de tile. A legenda compartilha os tiles e os registros usados pelo mapa. O menu pausa a simulação e lê os marcadores do estado corrente.

O clarão de dano muda o fundo do VDP por 12 interrupções de vídeo, cerca de 200 ms em 60 Hz ou 240 ms em 50 Hz. Teto e piso usam pixels transparentes para mostrar o clarão dentro do cenário. Ao final do efeito, o jogo restaura o fundo e silencia o canal C.

## Validação da campanha

- O WebMSX executou os três setores a 50 e 60 Hz. A rota passa pelos dois tipos de inimigo, as duas armas, a coleta de munição e chaves, a barreira da porta, o final e o retorno ao título.
- Os testes também verificaram partida e reinício, a diferença entre os alcances das armas, a mira e a oclusão atrás de uma porta, o PSG e a legenda e o mapa após mudanças na fase.
- A faixa da abertura repete a cada 22,4 s nos dois perfis. O teste verifica atividade nos três canais, percussão, animação dos medidores, repetição e silêncio após iniciar a campanha.
- A amostra de avanço no início do setor 1, com o monstro vivo, apresentou 14 quadros em um segundo no perfil de 60 Hz e 15 no de 50 Hz. O movimento respeita um intervalo mínimo de três interrupções de vídeo, e a cadência pode variar com o custo do quadro.
- O teste físico em um MSX1 original com cartucho ou flashcart continua pendente.

## Referências

- [BIOS e acesso à VRAM no MSX Technical Handbook](https://konamiman.github.io/MSX2-Technical-Handbook/md/Appendix1.html)
- [Configurações C-BIOS no manual do openMSX](https://openmsx.org/manual/setup.html)
- [Implementação do emulador WebMSX](https://github.com/ppeccin/WebMSX)
