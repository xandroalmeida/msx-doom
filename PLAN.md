# Plano para MSX1 com 64 KiB

O objetivo é preservar a exploração em primeira pessoa, a leitura de salas e corredores e o combate de um FPS em um MSX1 de fábrica. A primeira fase original já pode ser concluída no emulador.

## Plataforma e orçamento

| Recurso | Implementação atual |
| --- | --- |
| CPU | Z80 a aproximadamente 3,58 MHz. Coordenadas de ponto fixo 8.8 e tabelas geradas no build. |
| Vídeo | VDP da classe TMS9918 com 16 KiB de VRAM. SCREEN 2 a 256 × 192, com janela 3D de 256 × 128. |
| RAM | 64 KiB físicos. O estado do cartucho e o mapa mutável cabem no intervalo de 1 KiB em `C000h–C3FFh`. A pilha e a área de trabalho do BIOS usam o restante. |
| ROM | Cartucho linear de 16 KiB em `4000h–7FFFh`. O binário ocupa 14.820 bytes, incluindo alinhamento, e deixa 1.564 bytes na imagem. |
| Geometria | Mapa de 16 × 16 células, paredes ortogonais de altura uniforme, uma porta e 64 orientações de câmera. |
| Renderização | Um raio por coluna de 8 pixels. Paredes e objetos usam tiles pré-calculados. O jogo envia 512 nomes de tiles e uma linha de HUD para a página oculta e a apresenta no VBlank. |

As duas tabelas de nomes ficam em `1800h` e `1C00h` na VRAM. A profundidade da parede de cada coluna serve para ocultar o monstro e os outros objetos. Os objetos têm quatro tamanhos de tile e o contorno segue a resolução da grade. O tiro verifica as mesmas células sólidas usadas pelas paredes. A arma e o clarão usam sprites do VDP. O movimento ainda usa um intervalo mínimo de três interrupções de vídeo, que pode aumentar conforme o tempo de renderização.

## Marcos

1. **Movimento e vídeo** — verificados no WebMSX em 50 e 60 Hz com teclado, joystick, colisão e troca de páginas.
2. **Primeira fase jogável** — verificada no WebMSX em 50 e 60 Hz. O percurso inclui uma arma, um monstro que persegue e ataca, uma caixa de munição, uma porta bloqueada enquanto o monstro vive e uma saída. O jogador pode vencer, morrer e reiniciar. O teste isolado também verifica se a porta bloqueia visão, projeção e tiro. A marcha inicial com o monstro vivo atingiu 14 quadros em 60 Hz e 15 em 50 Hz no primeiro segundo, acima da meta de 12 nessa amostra.
3. **Tempo de quadro e hardware** — medir o pior trecho em sala aberta, corredor longo e giro contínuo. Fixar a cadência da simulação entre 50 e 60 Hz e verificar imagem, som e controles em um MSX1 físico com cartucho ou flashcart. Registrar modelo, padrão de vídeo e resultados.
4. **Geometria e conteúdo** — medir o custo de múltiplos inimigos, testar alturas distintas e visibilidade entre salas em uma geometria pequena. Reavaliar o tamanho do cartucho com os dados da fase.

## Referências

- [BIOS e acesso à VRAM no MSX Technical Handbook](https://konamiman.github.io/MSX2-Technical-Handbook/md/Appendix1.html)
- [Configurações C-BIOS no manual do openMSX](https://openmsx.org/manual/setup.html)
- [Implementação do emulador WebMSX](https://github.com/ppeccin/WebMSX)
