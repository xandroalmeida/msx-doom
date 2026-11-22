# Posto Umbra

FPS original inspirado em Doom para **MSX1 com 64 KiB de RAM**. A campanha tem três setores de 32 × 44 células, quatro portões por setor, 36 inimigos e duas armas. O cartucho linear ocupa 16 KiB.

## Fases

- **Depósito.** Pilhas de carga e corredores paralelos ligam a doca, a sala de bombas e o controle de evacuação.
- **Fundição.** As chaves ficam nas salas a oeste e abrem portões no lado leste. Desvios pelos corredores de serviço dão acesso a suprimentos.
- **Reator.** Três alas compridas, com passagens paralelas e galerias estreitas, ligam a entrada ao transmissor de superfície.

## Abertura

**Sinal de Umbra** é o tema original da tela de título. O arranjo em 7/8 usa os três canais de tom do PSG e mistura percussão de ruído ao baixo. As barras na tela acompanham os canais. A faixa repete a cada 22,4 segundos e silencia ao iniciar a campanha. Ao voltar ao título, ela recomeça do primeiro compasso.

## Jogar

Arraste `build/posto-umbra.rom` para o [WebMSX em modo MSX1 com 64 KiB](https://webmsx.org/?MACHINE=MSX1A&RAMNORMAL_SIZE=64), ou carregue a mesma ROM no [openMSX](https://openmsx.org/manual/setup.html#cbios).

```sh
openmsx -machine C-BIOS_MSX1 -cart build/posto-umbra.rom
```

| Ação | Teclado | Joystick da porta 1 |
| --- | --- | --- |
| Começar, avançar de setor ou confirmar uma nova tentativa | Espaço | Botão A |
| Avançar ou recuar | ↑ / ↓ | Cima / baixo |
| Girar | ← / → | Esquerda / direita |
| Atirar ou manter uma sequência de disparos | Espaço | Botão A |
| Trocar de arma | X | B + cima |
| Abrir a porta | Shift | Botão B |
| Abrir ou fechar o menu de pausa | M | A + B |
| Mostrar ou ocultar o minimapa durante a partida | N | B + baixo |
| Alternar entre legenda e mapa | ← / → | Esquerda / direita |
| Rolar o mapa de pausa | ↑ / ↓ | Cima / baixo |
| Reiniciar o setor durante a partida | R | — |

A pistola gasta uma carga e alcança alvos distantes. A arma de pulso gasta duas cargas e causa dois pontos de dano em alcance curto. As caixas amarelas fornecem oito cargas, e os corações no cenário recuperam até dois pontos de vida. O bruto roxo aguenta mais disparos e se aproxima mais rápido que o monstro vermelho.

Encontre as quatro chaves de cada setor, abra os portões correspondentes e siga até o sinal verde. Você pode passar pelos inimigos ou enfrentá-los para alcançar as chaves e os suprimentos. A vida e a munição inicial são repostas a cada setor e em cada nova tentativa. Depois da tela final, Espaço volta ao título.

A visão 3D ocupa 256 × 184 pixels. A última linha concentra os corações, a munição, a arma, o setor e a dica de objetivo em uma fonte pixel art inspirada em terminais. Ao sofrer dano, um coração fica vazado, o cenário pisca em vermelho e o PSG toca um som breve de impacto. Os cinco corações aparecem vazados na tela de derrota.

## Legenda e mapa

O minimapa no canto superior direito acompanha o jogador em tempo real. Mostra apenas o terreno, o estado das passagens e a seta da sua posição e direção. **N** alterna a exibição durante a partida. A preferência vale até desligar ou recarregar o cartucho.

**M** pausa na legenda. **→** abre o mapa na altura do jogador, **↑/↓** mostram outras áreas, **←** volta à legenda e **M** retoma a partida. A seta branca indica a posição e a direção do jogador. O mapa mostra portões abertos e fechados, inimigos, munição, cura, chaves e a saída.

Os símbolos da legenda e do mapa são gerados com os tiles da fase a partir de `TERRAIN` e `OBJECT_ART`. Ao mudar ou adicionar um tipo de terreno ou objeto visível, atualize esses registros e o teste. Para um novo objeto dinâmico, atualize também o desenho de marcadores no menu.

## Compilar

Use Python 3.8 ou superior e [pyz80](https://github.com/simonowen/pyz80).

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install pyz80==1.3.0
python tools/build.py
```

O build valida a ordem dos portões e a rota de cada setor, gera as tabelas e preenche a imagem até 16 KiB. A opção `--assembler caminho/pyz80.py` permite usar diretamente o script do montador.

## Repetir a validação

O teste usa o núcleo do [WebMSX 6.0.8 C-BIOS](https://github.com/ppeccin/WebMSX/blob/master/release/stable/6.0/cbios/embedded/wmsx.js) com Node.js 20, em MSX1 de 64 KiB e clock padrão.

```sh
curl -fL https://raw.githubusercontent.com/ppeccin/WebMSX/master/release/stable/6.0/cbios/embedded/wmsx.js -o build/wmsx.js
node tests/webmsx.cjs build/wmsx.js build/combate.ppm build/legenda.ppm build/mapa.ppm build/final.ppm build/sinal-de-umbra.wav build/titulo.ppm build/vida.ppm build/dano.ppm
```

Os arquivos de captura são opcionais. O WAV vem do PSG emulado. O teste verifica a música a 50 e 60 Hz, percorre a campanha com os controles do jogo e mede o tempo de navegação com os inimigos desativados. Uma arena separada verifica armas, tiros em sequência, oclusão, cura, derrota e os efeitos de dano. O teste do minimapa cobre os dois atalhos, movimento, direção e a ausência de ícones de itens e inimigos. A validação em um MSX1 físico ainda está pendente.

## Código

- [Plano e orçamento](PLAN.md)
- [Cartucho, movimento e renderização de paredes](src/posto-umbra.z80)
- [Campanha, carregamento de setores e som](src/campaign.z80)
- [Reprodução da abertura no PSG](src/opening.z80)
- [Partitura em formato editável](tools/opening.py)
- [Combate e interação](src/combat.z80)
- [Projeção de objetos e HUD](src/objects.z80)
- [Legenda e mapa](src/menu.z80)
- [Mapas e validação das rotas](tools/levels.py)
- [Arte e geração de tabelas](tools/tables.py)
- [Teste automatizado no WebMSX](tests/webmsx.cjs)
