# AGENTS.md

## Projeto

Posto Umbra é um jogo original para MSX1 com 64 KiB de RAM. A ROM atual é um cartucho linear de 32 KiB. O código do cartucho está em Z80 e as ferramentas Python geram a arte, as tabelas, as partituras e os mapas que o montador incorpora à ROM.

## Onde trabalhar

- Use [README.md](README.md) para história, jogabilidade, controles e imagens do jogo. Atualize os trechos em português, inglês e espanhol quando mudar informações comuns aos jogadores.
- Use [docs/TECNICO.md](docs/TECNICO.md) para compilação, emuladores, testes e referências de implementação. Registre orçamento e resultados medidos em [PLAN.md](PLAN.md).
- Use [src/](src/) para rotinas do cartucho, [tools/](tools/) para os dados e seus geradores e [tests/webmsx.cjs](tests/webmsx.cjs) para regressões em emulador.
- Edite `tools/levels.py` e `tools/additional_sectors.py` para alterar os mapas. As artes da embalagem ficam em [docs/packaging/](docs/packaging/) e as capturas do jogo em [docs/screenshots/](docs/screenshots/).
- O hotsite fica em [site/](site/) e usa a ROM da release estável mais recente. Ao publicar um lançamento, anexe a ROM com o nome `posto-umbra.rom` para que o [fluxo do GitHub Pages](.github/workflows/pages.yml) atualize o emulador e o download.

## Cuidados com mudanças

- Confira os limites atuais de ROM, RAM e VRAM ao alterar dados ou rotinas do cartucho. Use o total reportado por `tools/build.py` para atualizar o orçamento após mudanças na ROM.
- O build valida as rotas pelas chaves e portões, as faixas de complexidade e a munição dos mapas. O portão final usa o marcador `4` e a chave `d`. Mantenha essa relação com o HUD ao editar um mapa.
- Confira o comportamento nas entradas normais do jogo ao mexer em controles, pausa, combate ou campanha. A suíte exercita teclado e joystick, os modos de 50 e 60 Hz e o retorno ao título.
- Mantenha código, dados e artes editáveis no repositório. Os arquivos gerados pela compilação e as capturas de teste ficam em `build/`. O ambiente Python local fica em `.venv/`.

## Validação

Com o ambiente e o montador configurados, rode a partir da raiz do repositório.

```sh
source .venv/bin/activate
python tools/build.py
node tests/webmsx.cjs build/wmsx.js
```

O [guia técnico](docs/TECNICO.md) inclui a instalação do montador e o download da versão do WebMSX esperada pela suíte. Em mudanças apenas de documentação, confira os caminhos, as imagens e os comandos citados.
