# Posto Umbra

FPS original inspirado em Doom para MSX1 com 64 KiB de RAM. A primeira fase jogável tem um monstro, uma arma com munição limitada e uma saída atrás de uma porta trancada.

## Jogar

Use a ROM em `build/posto-umbra.rom`. Arraste o arquivo para o [WebMSX em modo MSX1 com 64 KiB](https://webmsx.org/?MACHINE=MSX1A&RAMNORMAL_SIZE=64), ou abra a mesma ROM no [openMSX](https://openmsx.org/manual/setup.html#cbios):

```sh
openmsx -machine C-BIOS_MSX1 -cart build/posto-umbra.rom
```

| Ação | Teclado | Joystick da porta 1 |
| --- | --- | --- |
| Avançar e recuar | ↑ e ↓ | Cima e baixo |
| Girar | ← e → | Esquerda e direita |
| Atirar | Espaço | Botão A |
| Abrir a porta | Shift | Botão B |
| Reiniciar após vencer ou morrer | Espaço | Botão A |

Comece com dois tiros. A caixa amarela fornece mais quatro. Aproxime-se da porta depois de eliminar o monstro, abra-a e siga até o sinal verde. Se o monstro alcançar você, ele pode causar dano repetidamente. Com a vida zerada, pressione Espaço para tentar de novo.

## Compilar

Use Python 3.8 ou superior e [pyz80](https://github.com/simonowen/pyz80).

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install pyz80==1.3.0
python tools/build.py
```

O build gera as tabelas, monta o Z80, confere o cabeçalho `AB` e preenche a imagem até 16 KiB. A opção `--assembler caminho/pyz80.py` permite usar diretamente o script do montador.

## Repetir o teste no emulador

O teste usa o núcleo do [WebMSX 6.0.8 C-BIOS](https://github.com/ppeccin/WebMSX/blob/master/release/stable/6.0/cbios/embedded/wmsx.js) com Node.js 20, em MSX1 de 64 KiB, com clock padrão e perfis de 50 e 60 Hz.

```sh
curl -fL https://raw.githubusercontent.com/ppeccin/WebMSX/master/release/stable/6.0/cbios/embedded/wmsx.js -o build/wmsx.js
node tests/webmsx.cjs build/wmsx.js build/posto-umbra.ppm
```

O último argumento é opcional e grava um quadro com o monstro e o clarão do tiro. O teste cobre teclado, joystick, carregamento de VRAM, acerto, tiro bloqueado pela porta, clarão, PSG, perseguição, ataque, coleta, vitória, derrota e reinício. No primeiro segundo de avanço com o monstro vivo, a build exibiu 14 quadros a 60 Hz e 15 a 50 Hz. O teste em um MSX1 físico continua pendente.

## Código

- [Plano e orçamento](PLAN.md)
- [Cartucho, movimento e renderização das paredes](src/posto-umbra.z80)
- [Combate, interação e regras da fase](src/combat.z80)
- [Projeção de objetos e HUD](src/objects.z80)
- [Mapa, tiles e tabelas de projeção](tools/tables.py)
- [Teste automatizado no WebMSX](tests/webmsx.cjs)
