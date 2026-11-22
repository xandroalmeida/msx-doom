# Posto Umbra para MSX1 com 64 KiB

A campanha original está jogável do título ao final. Ela preserva exploração em primeira pessoa, mira, combate, controle de munição e uso de chaves em um cartucho de 16 KiB.

## Plataforma e orçamento

| Recurso | Implementação |
| --- | --- |
| CPU | Z80 a aproximadamente 3,58 MHz. Coordenadas de ponto fixo 8.8 e tabelas geradas no build. |
| Vídeo | VDP da classe TMS9918 com 16 KiB de VRAM. SCREEN 2 a 256 × 192, com visão 3D de 256 × 184 e HUD na última linha. |
| RAM | MSX1 de 64 KiB. O cartucho usa `C080h–F1FFh`. O terreno ocupa uma página por linha, com inimigos e objetos nos espaços livres após as duas primeiras linhas. A zona de trabalho do BIOS fica acima dos buffers do cartucho. |
| ROM | Cartucho linear em `4000h–7FFFh`. O binário ocupa 16.150 bytes, incluindo alinhamento, e deixa 234 bytes na imagem de 16 KiB. |
| Geometria | Três mapas de 32 × 44 células e paredes ortogonais de altura uniforme. A ROM guarda o terreno em sequências de células iguais. O jogo expande o setor ativo em RAM e abre portões individualmente. |
| Renderização | 32 raios por quadro e 64 direções de câmera. Os raios avançam em passos maiores depois das primeiras duas células. Inclinações na mesma face de pedra usam máscaras de dois ou quatro pixels no topo e na base. Os objetos são desenhados de trás para frente e usam a profundidade para oclusão. |
| Som | PSG integrado. O tema original da abertura usa três canais de tom e ruído. Durante a campanha, a arma usa ruído no canal A, interações e saída usam o canal B, e o impacto ao sofrer dano usa o canal C. |

As duas tabelas de nomes ficam em `1800h` e `1C00h` na VRAM. O jogo envia os 768 nomes de tiles à página oculta antes de apresentá-la no VBlank. O minimapa sobrepõe 7 × 5 células de terreno no canto superior direito e acompanha a posição e a direção do jogador. O mapa de pausa exibe 16 linhas por vez com os marcadores do estado corrente. Cada setor admite até 14 inimigos e 17 objetos de cenário.

O clarão de dano muda o fundo do VDP por 12 interrupções de vídeo, cerca de 200 ms em 60 Hz ou 240 ms em 50 Hz. Teto e piso usam pixels transparentes para mostrar o clarão dentro do cenário. Ao final do efeito, o jogo restaura o fundo e silencia o canal C.

## Validação da campanha

- O WebMSX percorreu os três setores a 50 e 60 Hz com os comandos de movimento e interação. A rota passa pelos quatro pares de chave e portão de cada fase, pelo final e pelo retorno ao título.
- A navegação guiada com os inimigos desativados levou 2min27s, 2min20s e 2min36s a 60 Hz com o minimapa ativo.
- Uma arena isolada verificou as duas espécies de inimigos, os alcances das armas, a oclusão atrás de portas e a coleta de munição e cura. Os testes também verificaram derrota e reinício, a rolagem do mapa e a combinação de sons do PSG.
- A faixa da abertura repete a cada 22,4 s nos dois perfis. O teste verifica atividade nos três canais, percussão, animação dos medidores, repetição e silêncio após iniciar a campanha.
- Na arena de teste, o primeiro segundo de combate apresentou 11 quadros nos dois perfis com o minimapa ativo. O teste de vídeo verifica as máscaras das inclinações e as linhas adicionais das paredes próximas.
- O teste físico em um MSX1 original com cartucho ou flashcart continua pendente.

## Referências

- [BIOS e acesso à VRAM no MSX Technical Handbook](https://konamiman.github.io/MSX2-Technical-Handbook/md/Appendix1.html)
- [Configurações C-BIOS no manual do openMSX](https://openmsx.org/manual/setup.html)
- [Implementação do emulador WebMSX](https://github.com/ppeccin/WebMSX)
