# Posto Umbra

FPS original inspirado em Doom para **MSX1 com 64 KiB de RAM**. A campanha tem três setores, dois tipos de inimigo, duas armas, chaves e uma saída final. O cartucho linear ocupa 16 KiB.

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
| Atirar | Espaço | Botão A |
| Trocar de arma | X | B + cima |
| Abrir a porta | Shift | Botão B |
| Abrir ou fechar o menu de pausa | M | A + B |
| Alternar entre legenda e mapa | ← / → | Esquerda / direita |
| Reiniciar o setor durante a partida | R | — |

A pistola gasta uma carga e alcança alvos distantes. A arma de pulso gasta duas cargas e causa dois pontos de dano em alcance curto. A caixa amarela acrescenta quatro cargas. O bruto roxo aguenta mais disparos e se aproxima mais rápido que o monstro vermelho.

Elimine os inimigos, encontre a chave nos setores 2 e 3, abra a porta e siga até o sinal verde. A vida e a munição inicial são repostas a cada setor e em cada nova tentativa. Depois da tela final, Espaço volta ao título.

No HUD, cada coração vermelho representa um ponto de vida. Ao sofrer dano, um coração fica vazado, o cenário pisca em vermelho e o PSG toca um som breve de impacto. Os cinco corações aparecem vazados na tela de derrota.

## Legenda e mapa

**M** pausa na legenda. **→** mostra o mapa, **←** volta à legenda e **M** retoma a partida. A seta branca marca a posição e a direção cardinal mais próxima do olhar. O mapa acompanha a porta, os inimigos, a caixa de munição e a chave. Se a seta dividir a célula com outro marcador, a posição do jogador fica visível por cima.

Os símbolos da legenda e do mapa são gerados com os tiles da fase a partir de `TERRAIN` e `OBJECT_ART`. Ao mudar ou adicionar um tipo de terreno ou objeto visível, atualize esses registros e o teste. Para um novo objeto dinâmico, atualize também o desenho de marcadores no menu.

## Compilar

Use Python 3.8 ou superior e [pyz80](https://github.com/simonowen/pyz80).

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install pyz80==1.3.0
python tools/build.py
```

O build valida a rota de cada setor, gera as tabelas e preenche a imagem até 16 KiB. A opção `--assembler caminho/pyz80.py` permite usar diretamente o script do montador.

## Repetir a validação

O teste usa o núcleo do [WebMSX 6.0.8 C-BIOS](https://github.com/ppeccin/WebMSX/blob/master/release/stable/6.0/cbios/embedded/wmsx.js) com Node.js 20, em MSX1 de 64 KiB e clock padrão.

```sh
curl -fL https://raw.githubusercontent.com/ppeccin/WebMSX/master/release/stable/6.0/cbios/embedded/wmsx.js -o build/wmsx.js
node tests/webmsx.cjs build/wmsx.js build/combate.ppm build/legenda.ppm build/mapa.ppm build/final.ppm build/sinal-de-umbra.wav build/titulo.ppm build/vida.ppm build/dano.ppm
```

Os arquivos de captura são opcionais. O WAV é gravado a partir do áudio gerado pelo PSG emulado. O teste verifica o tempo do ciclo musical nos perfis de 50 e 60 Hz, a repetição, a retomada do título e a liberação dos canais para os efeitos da campanha. Em seguida, percorre os três setores e verifica armas, chave, porta, inimigos, derrota, reinício, mapa, os corações do HUD e o clarão de dano no cenário. Também verifica que o som de dano e o disparo podem tocar juntos. No primeiro segundo de avanço do setor 1 com o monstro vivo, a ROM apresentou 14 quadros a 60 Hz e 15 quadros a 50 Hz. A validação em um MSX1 físico ainda está pendente.

## Código

- [Plano e orçamento](PLAN.md)
- [Cartucho, movimento e renderização de paredes](src/posto-umbra.z80)
- [Campanha, carregamento de setores e som](src/campaign.z80)
- [Reprodução da abertura no PSG](src/opening.z80)
- [Partitura em formato editável](tools/opening.py)
- [Combate e interação](src/combat.z80)
- [Projeção de objetos e HUD](src/objects.z80)
- [Legenda e mapa](src/menu.z80)
- [Mapas, arte e geração de dados](tools/tables.py)
- [Teste automatizado no WebMSX](tests/webmsx.cjs)
