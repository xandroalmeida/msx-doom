# Guia técnico do Posto Umbra

[Voltar ao README do jogo](../README.md) · [Plano e orçamento](../PLAN.md) · [Orientações de manutenção](../AGENTS.md)

## Plataforma

| Recurso | Implementação |
| --- | --- |
| Máquina | MSX1 com 64 KiB de RAM e Z80 a aproximadamente 3,58 MHz |
| Vídeo | VDP compatível com TMS9918, 16 KiB de VRAM, SCREEN 2 a 256 × 192 |
| Cartucho | ROM linear de 32 KiB mapeada em `4000h–BFFFh` |
| Som | PSG. O canal A toca os disparos, B toca a melodia e C toca o baixo durante a campanha. Os efeitos de interação e dano usam B e C temporariamente. |

O cabeçalho do cartucho aponta para a rotina de entrada. A inicialização mapeia a segunda página no mesmo slot ou subslot da primeira. O build informa quantos bytes do cartucho estão ocupados e preenche a imagem até 32 KiB.

## Compilar

Na raiz do repositório, use Python 3.8 ou superior e o montador pyz80.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install pyz80==1.3.0
python tools/build.py
```

A ROM é criada em `build/posto-umbra.rom`. O montador também escreve o mapa de símbolos `build/posto-umbra.sym`, usado pelos testes. Para usar uma cópia local do montador, passe `--assembler caminho/pyz80.py` ao script de build. [Código do pyz80](https://github.com/simonowen/pyz80)

## Executar

Carregue a ROM no WebMSX com 64 KiB de RAM ou abra no openMSX com o C-BIOS. [WebMSX no perfil MSX1](https://webmsx.org/?MACHINE=MSX1A&RAMNORMAL_SIZE=64) · [Configuração do openMSX](https://openmsx.org/manual/setup.html#cbios)

```sh
openmsx -machine C-BIOS_MSX1 -cart build/posto-umbra.rom
```

## Hotsite e releases

O hotsite fica em `site/`. Depois de compilar a ROM, use estes comandos na raiz para abrir uma prévia local.

```sh
python tools/build_site.py
python -m http.server 8765 --directory build/site
```

O atalho `make serve` faz os dois passos, compila a ROM se ela faltar e serve o site em `http://localhost:8765/` até o Ctrl+C. Use `PORT=9000` para trocar a porta.

O fluxo do GitHub Pages busca a release estável mais recente, empacota seu arquivo `posto-umbra.rom` e publica o site. O emulador e o download usam a mesma ROM. O site informa a versão e usa o hash do binário no endereço para distinguir versões no cache. [Hotsite](https://xandroalmeida.github.io/msx-doom/) · [Fluxo do GitHub Pages](../.github/workflows/pages.yml)

Para lançar uma versão, use uma tag com prefixo `v`, compile a ROM do commit marcado e anexe `build/posto-umbra.rom` com esse nome exato à release estável antes de publicá-la. O ambiente `github-pages` permite implantar a partir de `main` e das tags `v*`. A publicação dispara a atualização do hotsite. [Releases](https://github.com/xandroalmeida/msx-doom/releases)

## Rodar os testes

Compile a ROM primeiro. A suíte usa Node.js 20 e o núcleo WebMSX 6.0.8 C-BIOS. O teste confere o SHA-256 do núcleo antes de executar.

```sh
curl -fL https://raw.githubusercontent.com/ppeccin/WebMSX/master/release/stable/6.0/cbios/embedded/wmsx.js -o build/wmsx.js
node tests/webmsx.cjs build/wmsx.js
```

Os argumentos opcionais abaixo geram capturas PPM e a gravação do PSG em WAV.

```sh
node tests/webmsx.cjs build/wmsx.js \
  build/combate.ppm build/legenda.ppm build/mapa.ppm build/final.ppm \
  build/sinal-de-umbra.wav build/titulo.ppm build/vida.ppm build/dano.ppm \
  build/creditos.ppm build/voz-na-serra.wav
```

A suíte roda a 50 e 60 Hz e cobre a abertura, o áudio, os controles, as três dificuldades, os 21 mapas, a progressão da campanha e o bloqueio da saída enquanto houver inimigos. Os testes de navegação percorrem as fases com os inimigos marcados como derrotados. Uma arena separada exercita o combate e a regra de eliminação. A validação em um MSX1 físico está pendente. [Núcleo C-BIOS usado nos testes](https://github.com/ppeccin/WebMSX/blob/master/release/stable/6.0/cbios/embedded/wmsx.js)

## Organização do código

| Área | Arquivos |
| --- | --- |
| Entrada do cartucho, movimento, vídeo e raycasting | [posto-umbra.z80](../src/posto-umbra.z80) |
| Sorteio, carregamento e andamento da campanha | [campaign.z80](../src/campaign.z80) |
| Combate, portões e condição da missão | [combat.z80](../src/combat.z80), [mission.z80](../src/mission.z80) |
| Projeção, HUD, bússola e abas da pausa | [objects.z80](../src/objects.z80), [compass.z80](../src/compass.z80), [menu.z80](../src/menu.z80) |
| Arte e música da abertura | [title_art.py](../tools/title_art.py), [opening.py](../tools/opening.py), [opening.z80](../src/opening.z80) |
| Rádio, diálogo, créditos e tema do final | [ending.py](../tools/ending.py), [ending_art.py](../tools/ending_art.py), [ending.z80](../src/ending.z80), [opening.py](../tools/opening.py) |
| Partituras e reprodução na campanha | [music.py](../tools/music.py), [music.z80](../src/music.z80) |
| Geometria, validação de rotas e tabelas | [levels.py](../tools/levels.py), [additional_sectors.py](../tools/additional_sectors.py), [tables.py](../tools/tables.py) |
| Build e regressão em emulador | [build.py](../tools/build.py), [webmsx.cjs](../tests/webmsx.cjs) |

### Mapas e progressão

A ROM guarda o terreno em blocos de 3 × 3 células com um dicionário compartilhado. Em RAM, o mapa ativo ocupa uma página por linha. O código usa o restante das páginas para armazenar entidades e colunas de parede pré-calculadas.

O build valida as quatro faixas de complexidade, a ordem dos pares de chaves e portões, a conectividade e a munição disponível. Os mapas usam dois a quatro portões. O marcador `4` e a chave `d` identificam o último portão e acionam a indicação de saída ou de combate. Os pares válidos usam os portões `14`, `124` ou `1234`. Dentro de cada faixa, o comprimento da rota obrigatória determina a ordem, com combate e suprimentos como desempate.

As células iniciais são reservadas antes de posicionar as entidades. Inimigos, suprimentos e chaves se deslocam sobre piso livre durante o sorteio. Os portões fechados preservam a região de cada chave. Reiniciar a fase reaproveita a semente.

Os símbolos do mapa e da legenda vêm de `TERRAIN` e `OBJECT_ART` em `tables.py`. Ao adicionar um objeto dinâmico, atualize o desenho dos marcadores em `menu.z80` e a verificação correspondente na suíte.

### Vídeo e áudio

Os tiles do jogo, a arte da abertura e os bancos do final ficam compactados na ROM pelo formato de [pack.py](../tools/pack.py). O cartucho os descompacta numa área de RAM do mapa, recarregada a cada setor, e envia o resultado à VRAM com a tela apagada. O renderizador calcula 32 raios para 64 direções da câmera. As tabelas de nomes alternam entre `1800h` e `1C00h` na VRAM a cada quadro apresentado. O áudio da campanha reutiliza compassos idênticos e um dicionário de valores de frequência e volume. O plano detalha o orçamento de RAM e ROM, as rotinas de vídeo e os resultados de validação. [Plano e orçamento](../PLAN.md)
