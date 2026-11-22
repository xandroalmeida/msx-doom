const assert = require("node:assert/strict");
const { createHash } = require("node:crypto");
const { readFileSync, writeFileSync } = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const [, , emulatorPath, snapshotPath, legendPath, mapPath] = process.argv;
if (!emulatorPath) {
    console.error("Uso: node tests/webmsx.cjs caminho/para/wmsx.js [combate.ppm] [legenda.ppm] [mapa.ppm]");
    process.exit(1);
}

const emulator = readFileSync(emulatorPath);
assert.equal(
    createHash("sha256").update(emulator).digest("hex"),
    "b620f8c812638bed93c5cfb88ddda010ff04d120b7e655e24468257cd4568a40",
    "Use a distribuição WebMSX 6.0.8 C-BIOS indicada no README.",
);
const cartridge = readFileSync(path.join(__dirname, "../build/posto-umbra.rom"));
const symbols = readFileSync(path.join(__dirname, "../build/posto-umbra.sym"), "utf8");
function romAddress(label) {
    const match = symbols.match(new RegExp(`^([0-9a-f]+)=${label}$`, "im"));
    return Number.parseInt(match[1], 16);
}
function romTiles(label, length) {
    const offset = romAddress(label) - 0x4000;
    return cartridge.subarray(offset, offset + length);
}
const creatureTiles = new Set(romTiles("creature_tiles", 30));
creatureTiles.delete(0);
const terrain = romTiles("terrain_tiles", 4);
const playerArrows = romTiles("map_arrows", 4);
const visibleObjects = ["creature_tiles", "ammo_tiles", "exit_tiles"].map((label) => romTiles(label, 1)[0]);

// Start the authentic machine and VDP, with a minimal host for the video output.
const core = new vm.Script(
    emulator.toString().replace(/WMSX\.preLoadImagesAndStart\(\);\s*$/, "void 0;"),
    { filename: "wmsx.js" },
);

function boot(frequency) {
    const frame = {};
    const noop = () => {};
    const api = {
        console, performance, atob, btoa,
        navigator: {},
        matchMedia: () => ({ matches: false }),
        location: { search: "" },
        document: {
            head: { appendChild: noop },
            documentElement: { classList: { toggle: noop } },
            getElementById: noop,
            createElement(tag) {
                if (tag !== "canvas") return {};
                return {
                    getContext: () => ({
                        createImageData: (width, height) => ({
                            width, data: new Uint8ClampedArray(width * height * 4),
                        }),
                        putImageData: (image, x, y, left, top, width, height) =>
                            Object.assign(frame, { image, width, height }),
                    }),
                };
            },
        },
    };
    api.window = api;
    core.runInNewContext(api);
    const { WMSX, wmsx } = api;
    const pal = frequency === 50;
    Object.assign(WMSX, {
        MACHINE: pal ? "MSX1E" : "MSX1A",
        RAMNORMAL_SIZE: 64,
        BOOT_DURATION_AUTO: 0,
        Z80_CLOCK_MODE: 1,
        VDP_CLOCK_MODE: 1,
    });
    const machine = new wmsx.Machine();
    const inputs = { keys: 0, stick: 0, shift: false, menu: false };
    machine.getControllersSocket().connectControls({
        resetControllers: noop,
        readKeyboardPort(row) {
            if (row === 8) return 255 ^ inputs.keys;
            if (row === 6 && inputs.shift) return 254;
            if (row === 4 && inputs.menu) return 251;
            return 255;
        },
        readControllerPort: (port) => port === 0 ? 255 ^ inputs.stick : 255,
        writeControllerPin8Port: noop,
    });
    machine.getVideoClockSocket().connectClock({
        getRealTime: () => 0,
        getVSynchNativeFrequency: () => frequency,
        setVSynch: noop,
        setFrequency: noop,
    });
    machine.getVideoSocket().connectMonitor({
        connectInternalVideoSignal(signal) { signal.connectMonitor(this); },
        newFrame: noop,
        setDisplayMetrics: noop,
        setOutputAutoMode: noop,
        setDebugMode: noop,
        signalOff: noop,
        showOSD: noop,
    });
    machine.socketsConnected();
    const main = pal ? "@cbios_main_msx1_eu.rom" : "@cbios_main_msx1.rom";
    const bios = wmsx.EmbeddedFiles.get(main + " | @cbios_logo_msx1.rom");
    const slots = machine.getSlotSocket();
    const ram = new wmsx.SlotRAMNormal(new wmsx.ROM("ram", [], {}));
    assert.equal(ram.bytes.length, 64 * 1024);
    slots.insertSlot(new wmsx.SlotBIOS(new wmsx.ROM(bios.name, bios.content, {})), 0, true, true);
    const rom = new wmsx.ROM("posto-umbra.rom", Array.from(cartridge), { s: 0x4000 });
    slots.insertSlot(new wmsx.SlotPlainROM(rom), 1, true, true);
    slots.insertSlot(ram, 3, true, true);
    machine.powerOn();

    const read = (address) => machine.bus.read(address);
    const word = (address) => read(address) | (read(address + 1) << 8);
    return {
        frame, inputs, machine, read,
        write: (address, value) => machine.bus.write(address, value),
        run: (frames) => {
            for (let i = 0; i < frames; i++) machine.videoClockPulse();
        },
        xy: () => [word(0xc200), word(0xc202)],
        currentView: () => Buffer.from(Array.from({ length: 512 }, (_, i) => read(0xc000 + i))),
        video: () => {
            const state = machine.vdp.saveState();
            return {
                v9918: state.v1,
                regs: Buffer.from(state.r, "base64"),
                vram: Buffer.from(wmsx.Util.uncompressStringBase64ToInt8BitArray(state.vram)),
            };
        },
    };
}

function saveFrame(frame, filename) {
    const { image, width, height } = frame;
    const rgb = Buffer.alloc(width * height * 3);
    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            const source = (y * image.width + x) * 4;
            rgb.set(image.data.subarray(source, source + 3), (y * width + x) * 3);
        }
    }
    writeFileSync(filename, Buffer.concat([Buffer.from(`P6\n${width} ${height}\n255\n`), rgb]));
}

function checkVideo(run) {
    const { v9918, regs, vram } = run.video();
    assert.ok(v9918, "O VDP deve estar no modo MSX1.");
    assert.equal(run.machine.cpu.getZ80ClockMulti(), 1);
    assert.equal(regs[0] & 0x02, 0x02, "SCREEN 2 deve estar ativo.");
    assert.equal(regs[1] & 0x58, 0x40, "A tela deve estar ligada, com os bits de modo corretos.");
    assert.equal(regs[2], run.read(0xc205), "R2 deve apontar para a página apresentada.");
    const start = (regs[2] << 10) + 128;
    assert.deepEqual(vram.subarray(start, start + 512), run.currentView());
    const base = regs[2] << 10;
    const hud = Buffer.from(Array.from({ length: 32 }, (_, i) => run.read(0xc240 + i)));
    assert.deepEqual(vram.subarray(base + 21 * 32, base + 22 * 32), hud);
}

const state = {
    playerX: 0xc200, playerY: 0xc202, heading: 0xc204, page: 0xc205, shown: 0xc20b, life: 0xc20f,
    ammo: 0xc210, monster: 0xc211, monsterY: 0xc214, pickup: 0xc217,
    door: 0xc218, outcome: 0xc219, hint: 0xc21a, flash: 0xc21b, menu: 0xc225, map: 0xc300,
    wallDepth: 0xc260,
};
const up = 0x20;
const down = 0x40;
const right = 0x80;
const space = 1;
const startPosition = [0x0580, 0x0c80];
const doorNorthing = 0x0640;

function creatureTileCount(demo) {
    const { regs, vram } = demo.video();
    const start = (regs[2] << 10) + 128;
    return vram.subarray(start, start + 512).filter((tile) => creatureTiles.has(tile)).length;
}

function mapTile(demo, x, y) {
    return demo.currentView()[y * 32 + 2 + x];
}

function checkPlayerMarker(demo) {
    const [x, y] = demo.xy().map((coord) => coord >> 8);
    const direction = ((demo.read(state.heading) + 8) >> 4) & 3;
    assert.equal(mapTile(demo, x, y), playerArrows[direction]);
}

function press(demo, input, value) {
    demo.inputs[input] = value;
    demo.run(12);
    demo.inputs[input] = 0;
    demo.run(12);
}

function checkWallEdges(frequency, material, direction) {
    const demo = boot(frequency);
    demo.run(180);
    demo.write(state.monster, 0);
    demo.write(state.pickup, 0);
    const rotate = (x, y) => direction === 0 ? [x, y] : [15 - y, x];
    for (let y = 1; y < 15; y++) {
        for (let x = 1; x < 15; x++) {
            const [column, row] = rotate(x, y);
            // One block in front of a continuous wall of the same stone.
            const wall = y === 7 || (y === 10 && x === 5);
            demo.write(state.map + row * 16 + column, wall ? material : 0);
        }
    }
    const [x, y] = rotate(5, 12);
    demo.write(state.playerX + 1, x);
    demo.write(state.playerY + 1, y);
    demo.write(state.heading, direction);
    press(demo, "menu", true);
    press(demo, "menu", true);
    checkVideo(demo);

    const depths = Array.from({ length: 32 }, (_, i) => demo.read(state.wallDepth + i));
    const nearest = Math.min(...depths);
    const left = depths.indexOf(nearest);
    const right = depths.lastIndexOf(nearest);
    assert.ok(left > 0 && right < 31 && right - left > 1);
    const styles = romTiles("wall_styles", 8);
    const heights = romTiles("heights", romAddress("wall_columns") - romAddress("heights"));
    const tiles = romTiles("wall_columns", romAddress("terrain_tiles") - romAddress("wall_columns"));
    const view = demo.currentView();
    for (const [column, depth] of depths.entries()) {
        const edge = column === left || column === right;
        const style = material + (edge ? 4 : 0);
        const tile = tiles[(styles[style] + heights[depth]) * 16 + 7];
        assert.equal(view[7 * 32 + column], tile, `Borda indevida ou ausente na coluna ${column}.`);
    }
}

function holdUntil(demo, keys, condition, limit = 500) {
    demo.inputs.keys = keys;
    for (let i = 0; i < limit && !condition(); i++) demo.run(1);
    assert.ok(condition(), "A ação deve chegar ao estado esperado.");
    demo.inputs.keys = 0;
    demo.run(12);
}

function checkReset(demo) {
    assert.deepEqual(demo.xy(), startPosition);
    assert.equal(demo.read(state.heading), 0);
    assert.equal(demo.read(state.life), 5);
    assert.equal(demo.read(state.ammo), 2);
    assert.equal(demo.read(state.monster), 2);
    assert.equal(demo.read(state.pickup), 1);
    assert.equal(demo.read(state.door), 0);
    assert.equal(demo.read(state.map + 0x55), 3);
    assert.equal(demo.read(state.outcome), 0);
    checkVideo(demo);
}

for (const frequency of [60, 50]) {
    checkWallEdges(frequency, 1, 0);
    checkWallEdges(frequency, 2, 16);
    const demo = boot(frequency);
    const shown = () => demo.read(state.shown);
    const heading = () => demo.read(state.heading);
    const read = (key) => demo.read(state[key]);

    demo.run(180);
    checkReset(demo);
    assert.equal(read("page"), 6);
    assert.equal(shown(), 0, "A cena em repouso deve manter a mesma página.");
    const initialView = demo.currentView();
    assert.ok(new Set(initialView).size > 4, "O primeiro quadro deve conter a cena.");
    assert.ok(creatureTileCount(demo) > 0, "O monstro deve aparecer ao fundo ao iniciar.");

    press(demo, "menu", true);
    assert.equal(read("menu"), 1);
    assert.equal(demo.video().vram[0x1b00], 208, "Arma e mira devem sumir durante a pausa.");
    const legend = demo.currentView();
    for (const [index, tile] of terrain.entries()) assert.equal(legend[(5 + 2 * index) * 32 + 2], tile);
    const openDoor = legend[13 * 32 + 2];
    assert.notEqual(openDoor, terrain[3]);
    for (const [index, tile] of [playerArrows[0], ...visibleObjects].entries()) {
        assert.equal(legend[(5 + 2 * index) * 32 + 20], tile);
    }
    if (frequency === 60 && legendPath) saveFrame(demo.frame, legendPath);

    press(demo, "keys", right);
    assert.equal(read("menu"), 2);
    checkVideo(demo);
    checkPlayerMarker(demo);
    assert.equal(mapTile(demo, 0, 0), terrain[1]);
    assert.equal(mapTile(demo, 4, 10), terrain[2]);
    assert.equal(mapTile(demo, 5, 5), terrain[3]);
    assert.equal(mapTile(demo, 5, 8), visibleObjects[0]);
    assert.equal(mapTile(demo, 5, 11), visibleObjects[1]);
    assert.equal(mapTile(demo, 5, 3), visibleObjects[2]);
    if (frequency === 60 && mapPath) saveFrame(demo.frame, mapPath);
    press(demo, "keys", up | space);
    assert.deepEqual(demo.xy(), startPosition, "O mapa deve pausar o jogador.");
    assert.equal(read("ammo"), 2, "Espaço no mapa não deve disparar.");
    press(demo, "stick", 0x04);
    assert.equal(read("menu"), 1);
    assert.deepEqual(demo.currentView(), legend);
    press(demo, "menu", true);
    assert.equal(read("menu"), 0);
    assert.equal(demo.video().vram[0x1b00], 92);
    assert.deepEqual(demo.currentView(), initialView);

    // Hold the trigger across many simulation ticks. The first shot should hit
    // only once, show a flash in the VDP and put real noise on PSG channel A.
    demo.inputs.keys = space;
    let flashSeen = false;
    let soundSeen = false;
    for (let i = 0; i < 24; i++) {
        demo.run(1);
        if (read("flash")) {
            flashSeen ||= demo.video().vram[0x1b04] === 135;
            const psg = Buffer.from(demo.machine.psg.saveState().r, "base64");
            soundSeen ||= psg[6] === 7 && (psg[7] & 0x09) === 1 && psg[8] === 12;
        }
    }
    assert.ok(flashSeen && soundSeen, "O disparo deve ter clarão e ruído no PSG.");
    assert.equal(demo.video().vram[0x1b04], 209);
    assert.equal(Buffer.from(demo.machine.psg.saveState().r, "base64")[8], 0);
    assert.equal(read("ammo"), 1);
    assert.equal(read("monster"), 1);
    demo.inputs.keys = 0;
    demo.run(12);
    press(demo, "stick", 0x10); // Joystick A
    assert.equal(read("ammo"), 0);
    assert.equal(read("monster"), 0);
    press(demo, "keys", space);
    assert.equal(read("hint"), 4, "O HUD deve indicar a falta de munição.");

    const beforeWalking = shown();
    demo.inputs.keys = up;
    const pages = new Set();
    for (let i = 0; i < frequency; i++) {
        demo.run(1);
        pages.add(read("page"));
    }
    const walkingFps = (shown() - beforeWalking + 256) % 256;
    assert.ok(walkingFps >= 12, "Meta da POC durante marcha inicial: 12 quadros/s.");
    assert.deepEqual(pages, new Set([6, 7]));
    assert.equal(read("pickup"), 0);
    assert.equal(read("ammo"), 4);
    holdUntil(demo, up, () => demo.xy()[1] <= doorNorthing);
    assert.deepEqual(demo.xy(), [0x0580, doorNorthing], "A porta fechada deve barrar o jogador.");
    const blocked = shown();
    demo.inputs.keys = up;
    demo.run(30);
    demo.inputs.keys = 0;
    assert.equal(shown(), blocked, "O contato com a porta deve estabilizar a imagem.");
    assert.notDeepEqual(demo.currentView(), initialView);
    checkVideo(demo);

    press(demo, frequency === 60 ? "shift" : "stick", frequency === 60 ? true : 0x20);
    assert.equal(read("door"), 1);
    assert.equal(demo.read(state.map + 0x55), 0);
    press(demo, "menu", true);
    press(demo, "stick", 0x08);
    assert.equal(read("menu"), 2);
    checkPlayerMarker(demo);
    assert.notEqual(mapTile(demo, 5, 12), playerArrows[0], "O marcador deve sair da posição inicial.");
    assert.equal(mapTile(demo, 5, 5), openDoor);
    assert.equal(mapTile(demo, 5, 8), terrain[0], "O monstro derrotado deve sumir do mapa.");
    assert.equal(mapTile(demo, 5, 11), terrain[0], "A caixa coletada deve sumir do mapa.");
    press(demo, "menu", true);
    holdUntil(demo, up, () => read("outcome") === 2);
    assert.equal(read("life"), 5);
    const victoryView = demo.currentView();
    checkVideo(demo);
    press(demo, "keys", space);
    checkReset(demo);
    assert.notDeepEqual(demo.currentView(), victoryView);

    // Read the live creature through movement, contact attack and defeat.
    holdUntil(demo, up, () => read("outcome") === 1);
    assert.equal(read("life"), 0);
    assert.equal(read("monster"), 2);
    assert.notEqual(demo.read(state.monsterY), 0x80);
    assert.notDeepEqual(demo.currentView(), victoryView);
    checkVideo(demo);
    press(demo, "stick", 0x10);
    checkReset(demo);

    press(demo, "keys", down);
    assert.ok(demo.xy()[1] > startPosition[1], "A seta para baixo deve recuar.");

    const beforeTurn = demo.currentView();
    press(demo, "keys", right);
    const facingRight = heading();
    assert.ok(facingRight > 0 && facingRight < 16);
    assert.notDeepEqual(demo.currentView(), beforeTurn);
    checkVideo(demo);

    press(demo, "stick", 0x04); // Joystick left on port 1
    const leftTurn = (facingRight - heading() + 64) % 64;
    assert.ok(leftTurn > 0 && leftTurn < 8, "O joystick da porta 1 deve girar à esquerda.");
    checkVideo(demo);

    const beforeDiagonal = heading();
    const [, previousY] = demo.xy();
    press(demo, "stick", 0x0a); // Joystick down + right
    const diagonalTurn = (heading() - beforeDiagonal + 64) % 64;
    assert.ok(diagonalTurn > 0 && diagonalTurn < 8);
    assert.ok(demo.xy()[1] > previousY, "A diagonal deve recuar e girar juntas.");
    checkVideo(demo);
    holdUntil(demo, right, () => heading() >= 8 && heading() < 24);
    press(demo, "stick", 0x30); // A+B
    assert.equal(read("menu"), 1);
    assert.equal(read("ammo"), 2, "O atalho do joystick não deve disparar.");
    press(demo, "keys", right);
    assert.equal(read("menu"), 2);
    assert.equal(mapTile(demo, ...demo.xy().map((coord) => coord >> 8)), playerArrows[1]);
    press(demo, "stick", 0x30);
    assert.equal(read("menu"), 0);

    // Stage the same actor on the other side of the closed door. This isolates
    // occlusion, hitscan and enemy sight from the timing of the chase.
    const behindDoor = boot(frequency);
    behindDoor.run(180);
    behindDoor.write(state.playerY, doorNorthing & 255);
    behindDoor.write(state.playerY + 1, doorNorthing >> 8);
    behindDoor.write(state.monsterY + 1, 4);
    press(behindDoor, "shift", true);
    assert.equal(behindDoor.read(state.hint), 3, "Com o monstro vivo, a porta deve ficar trancada.");
    assert.equal(behindDoor.read(state.door), 0);
    assert.equal(creatureTileCount(behindDoor), 0, "A porta fechada deve encobrir o monstro.");
    press(behindDoor, "keys", space);
    assert.equal(behindDoor.read(state.ammo), 1);
    assert.equal(behindDoor.read(state.monster), 2, "O tiro deve parar na porta.");
    assert.equal(behindDoor.read(state.monsterY), 0x80, "A porta deve interromper a visão do monstro.");
    checkVideo(behindDoor);

    const arena = boot(frequency);
    arena.run(180);
    const farTiles = creatureTileCount(arena);
    arena.inputs.keys = up;
    arena.run(frequency);
    arena.inputs.keys = 0;
    const combatFps = arena.read(state.shown);
    let nearTiles = 0;
    for (let i = 0; i < 10; i++) {
        arena.run(1);
        nearTiles = Math.max(nearTiles, creatureTileCount(arena));
    }
    assert.ok(nearTiles > farTiles, "O monstro deve crescer na tela ao se aproximar.");
    press(arena, "menu", true);
    press(arena, "keys", right);
    const lifeOnPause = arena.read(state.life);
    const getEnemyPosition = () => [0xc212, state.monsterY].map((address) =>
        arena.read(address) | (arena.read(address + 1) << 8));
    const enemyPosition = getEnemyPosition();
    const enemyCell = enemyPosition.map((coordinate) => coordinate >> 8);
    const playerCell = arena.xy().map((coordinate) => coordinate >> 8);
    if (playerCell[0] === enemyCell[0] && playerCell[1] === enemyCell[1]) {
        checkPlayerMarker(arena);
    } else {
        assert.equal(mapTile(arena, ...enemyCell), visibleObjects[0]);
    }
    arena.run(180);
    assert.equal(arena.read(state.life), lifeOnPause);
    assert.deepEqual(getEnemyPosition(), enemyPosition);
    press(arena, "menu", true);
    const ammoBeforeShot = arena.read(state.ammo);
    arena.inputs.keys = space;
    let combatFrameSeen = false;
    for (let i = 0; i < 20; i++) {
        arena.run(1);
        if (arena.video().vram[0x1b04] === 135 && creatureTileCount(arena) > farTiles && !combatFrameSeen) {
            arena.run(1);
            combatFrameSeen = true;
            if (frequency === 60 && snapshotPath) saveFrame(arena.frame, snapshotPath);
        }
    }
    assert.equal(arena.read(state.ammo), ammoBeforeShot - 1);
    assert.equal(arena.read(state.monster), 1);
    assert.ok(combatFrameSeen, "Um disparo e o monstro devem aparecer no mesmo quadro.");
    assert.ok(combatFps >= 12);
    console.log(`MSX1 64 KiB, ${frequency} Hz: legenda, mapa, pausa, tiro, PSG, munição, oclusão, porta, vitória, derrota e reinício OK. Avanço com monstro vivo: ${combatFps} quadros apresentados em 1 s.`);
}
