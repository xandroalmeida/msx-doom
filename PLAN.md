# Posto Umbra para MSX1 com 64 KiB

A campanha está jogável do título ao final em 12 setores sorteados de um catálogo de 21. Ela preserva exploração em primeira pessoa, mira, combate, controle de munição e uso de chaves em um cartucho de 32 KiB.

## Plataforma e orçamento

| Recurso | Implementação |
| --- | --- |
| CPU | Z80 a aproximadamente 3,58 MHz. Coordenadas de ponto fixo 8.8 e tabelas geradas no build. |
| Vídeo | VDP da classe TMS9918 com 16 KiB de VRAM. SCREEN 2 a 256 × 192, com visão 3D de 256 × 184 e HUD na última linha. |
| RAM | MSX1 de 64 KiB. O cartucho usa `C080h–F1FFh`. O terreno ocupa uma página por linha. As sobras das páginas guardam inimigos, objetos e os modelos de colunas de parede. |
| ROM | Cartucho linear em `4000h–BFFFh`. O binário ocupa 29.631 bytes e deixa 3.137 bytes na imagem de 32 KiB. Uma compactação LZ simples, descompactada em RAM antes de cada envio à VRAM, reduziu os tiles do jogo e a arte da abertura de 8.608 para 3.178 bytes. A compactação das trilhas da campanha recuperou 3.034 bytes líquidos. |
| Geometria | 21 mapas de 32 × 44 células e paredes ortogonais de altura uniforme. A ROM guarda o terreno em blocos de 3 × 3 células que compartilham um dicionário. O jogo expande o setor ativo em RAM e abre portões individualmente. |
| Renderização | 32 raios por quadro e 64 direções de câmera. Os raios avançam em passos maiores depois das primeiras duas células. A projeção vertical das paredes é cerca de 30% maior que na versão anterior. Inclinações na mesma face de pedra usam máscaras de dois ou quatro pixels no topo e na base. Os objetos são desenhados de trás para frente e usam a profundidade para oclusão. |
| Som | PSG integrado. O tema da abertura usa três canais de tom e ruído. Na campanha, A toca os disparos, B toca a melodia e cede espaço às interações, e C toca o baixo e cede espaço ao som de dano. As três faixas reutilizam compassos idênticos e um dicionário de valores de frequência e volume para o PSG. |

As duas tabelas de nomes ficam em `1800h` e `1C00h` na VRAM. O jogo envia os 768 nomes de tiles à página oculta antes de apresentá-la no VBlank. A bússola tem um mostrador de 32 × 32 pixels com um sprite para o ponteiro, que usa 32 posições para as 64 direções da câmera. O minimapa sobrepõe 7 × 5 células de terreno no canto superior direito e acompanha a posição e a direção do jogador. A pausa tem abas para o mapa, a legenda e os comandos. O mapa exibe 16 linhas por vez com os marcadores do estado corrente. Cada setor admite até 16 inimigos e 17 objetos de cenário.

A ilustração da abertura ocupa os dois primeiros bancos de tiles do SCREEN 2. A animação percorre quatro quadros e atualiza nove tiles por mudança. A transferência dos bancos gráficos ao entrar ou sair do título ocorre com a tela apagada. O cartucho seleciona para a segunda página o mesmo slot ou subslot em que a BIOS iniciou a primeira. [MSX Technical Handbook](https://konamiman.github.io/MSX2-Technical-Handbook/md/Chapter5b.html)

Ao iniciar uma campanha, o jogo usa uma semente de 16 bits para sortear três setores de cada faixa de complexidade, sem repetição. As 12 fases seguem a ordem crescente da rota obrigatória, com resistência dos inimigos, munição e cura como desempate. Os primeiros mapas têm dois portões e rotas-base de 52 a 63 células. Os seguintes têm três portões e rotas de 91 a 149 células. Os intermediários e avançados têm quatro portões, com rotas de 192 a 251 e de 280 a 360 células, respectivamente. Para posicionar os objetos de cada setor, o jogo reserva as células iniciais e sorteia passos sobre piso livre, o que impede sobreposição e mantém as entidades na área dos portões correspondentes. As chaves podem andar até três células, e os inimigos e suprimentos, até seis. Reinícios preservam a semente do setor e a ordem da campanha.

Ao sair do último setor, o jogo apaga a tela e carrega a sala de rádio em pixel art. A arte ocupa 32 × 11 tiles com pixels duplicados, como a da abertura, e usa luz vinda da janela, com dois ou três tons por material e um contorno ciano refletido pelo rádio. O banco superior guarda 249 tiles da arte; o do meio guarda a fonte em três cores e as linhas inferiores da arte; o inferior guarda a fonte. Os três bancos são imagens compactadas. A animação troca nomes de tiles a cada quadro em cinco canais: o céu da janela (noite, aurora e nascer do sol), o farol do mastro, o traço do osciloscópio, as luzes TX e RX e os lábios do operador. As mensagens do posto e da central se alternam; cada uma limpa a área de texto e troca o rótulo. O texto é digitado a um caractere por tique de jogo, com pausas codificadas no roteiro. O leitor da abertura toca **Voz na Serra** em meios compassos de 8 passos com notas sustentadas. Ao voltar ao título, o jogo restaura o banco inferior de tiles usado pelos textos.

O clarão de dano muda o fundo do VDP por 12 interrupções de vídeo, cerca de 200 ms em 60 Hz ou 240 ms em 50 Hz. Teto e piso usam pixels transparentes para mostrar o clarão dentro do cenário. Ao final do efeito, o jogo restaura o fundo e devolve o canal C à trilha.

## Validação da campanha

- O WebMSX percorreu campanhas de 12 setores no Normal a 60 Hz e no Difícil a 50 Hz. O teste verificou as quatro faixas de complexidade, os pares de chave e portão de cada fase, o final e o retorno ao título. No final, conferiu a arte e a fonte na VRAM, a música nos três canais, o bloqueio de um Espaço acidental, a alternância das seis mensagens, o movimento do osciloscópio, o amanhecer nos créditos e a restauração dos tiles do título.
- Os testes das três dificuldades verificaram contagem, alcance de percepção, intervalo de ataque, variação entre sementes, acesso às chaves e repetição da distribuição ao reiniciar.
- Uma arena isolada verificou as duas espécies de inimigos, os alcances das armas, a oclusão atrás de portas e a coleta de munição e cura. Os testes também verificaram derrota e reinício, a rolagem do mapa, a navegação nas abas da pausa, a combinação de sons do PSG e o bloqueio da saída até eliminar todos os inimigos ativos.
- A faixa da abertura repete a cada 22,4 s nos dois perfis. O teste verifica atividade nos três canais, percussão, animação dos medidores, repetição e silêncio após iniciar a campanha.
- A trilha do Depósito repete a cada 25,6 s, e as da Fundição e do Reator, a cada 26,88 s. Os 1.168 quadros de áudio recompostos foram comparados com a ROM anterior e são idênticos. A suíte verifica os valores enviados ao PSG, a ordem dos compassos, os loops, a seleção por setor, os atalhos de áudio e a devolução dos canais depois da coleta ou do dano.
- Os quatro quadros da arte foram conferidos na VRAM com o cartucho em um subslot. A suíte confere a restauração da arte ao retornar ao título depois da campanha.
- Na arena de teste com o minimapa ativo, o primeiro segundo de combate apresentou 12 quadros a 50 Hz e 11 a 60 Hz. O teste de vídeo verifica as máscaras das inclinações, as linhas adicionais das paredes próximas e as posições do ponteiro da bússola.
- O teste físico em um MSX1 original com cartucho ou flashcart continua pendente.

## Referências

- [BIOS e acesso à VRAM no MSX Technical Handbook](https://konamiman.github.io/MSX2-Technical-Handbook/md/Appendix1.html)
- [Configurações C-BIOS no manual do openMSX](https://openmsx.org/manual/setup.html)
- [Implementação do emulador WebMSX](https://github.com/ppeccin/WebMSX)
