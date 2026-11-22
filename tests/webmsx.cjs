const assert = require("node:assert/strict");
const { createHash } = require("node:crypto");
const { readFileSync, writeFileSync } = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const [, , emulatorPath, snapshotPath, legendPath, mapPath, endingPath, openingPath, titlePath, healthPath, damagePath] = process.argv;
if (!emulatorPath) {
    console.error("Uso: node tests/webmsx.cjs wmsx.js [combate.ppm] [legenda.ppm] [mapa.ppm] [final.ppm] [abertura.wav] [titulo.ppm] [vida.ppm] [dano.ppm]");
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
const bruteTiles = new Set(romTiles("brute_tiles", 30));
bruteTiles.delete(0);
const terrain = romTiles("terrain_tiles", 4);
const playerArrows = romTiles("map_arrows", 4);
const visibleObjects = ["creature_tiles", "ammo_tiles", "exit_tiles", "brute_tiles", "key_tiles"]
    .map((label) => romTiles(label, 1)[0]);
const digitTiles = romTiles("hud_digits", 10);
const [heartEmpty, heartFull] = romTiles("hud_hearts", 2);
const weaponNames = romTiles("weapon_names", 14);
const miniTerrain = romTiles("mini_terrain", 4);
const difficultyNames = romTiles("difficulty_names", 24);
const frameStart = 0xc080;
const viewStart = 0xc100;
const hudStart = 0xc360;
const hudRow = 23;
const lifeOffset = 1;
const ammoOffset = 8;
const weaponOffset = 11;
const sectorOffset = 20;
const titlePicture = romTiles("title_picture", 16 * 32);
const titleMeterOffset = 14 * 32 + 5;
const titleDifficultyOffset = 16 * 32 + 15;

// Start the authentic machine and VDP, with a minimal host for the video output.
const core = new vm.Script(
    emulator.toString().replace(/WMSX\.preLoadImagesAndStart\(\);\s*$/, "void 0;"),
    { filename: "wmsx.js" },
);

function boot(frequency, subslot) {
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
    const inputs = { keys: 0, stick: 0, shift: false, menu: false, weapon: false, retry: false, minimap: false, music: false };
    machine.getControllersSocket().connectControls({
        resetControllers: noop,
        readKeyboardPort(row) {
            if (row === 8) return 255 ^ inputs.keys;
            if (row === 6 && inputs.shift) return 254;
            if (row === 4) return 255 ^ (inputs.menu ? 4 : 0) ^ (inputs.retry ? 128 : 0) ^ (inputs.minimap ? 8 : 0);
            if (row === 5) return 255 ^ (inputs.weapon ? 32 : 0) ^ (inputs.music ? 2 : 0);
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
    const cartridgeSlot = new wmsx.SlotPlainROM(rom);
    if (subslot === undefined) {
        slots.insertSlot(cartridgeSlot, 1, true, true);
    } else {
        const expanded = new wmsx.SlotExpanded();
        expanded.insertSubSlot(cartridgeSlot, subslot);
        slots.insertSlot(expanded, 1, true, true);
    }
    slots.insertSlot(ram, 3, true, true);
    machine.powerOn();

    let elapsed = 0;
    const read = (address) => machine.bus.read(address);
    const word = (address) => read(address) | (read(address + 1) << 8);
    return {
        frame, inputs, machine, read, elapsed: () => elapsed,
        write: (address, value) => machine.bus.write(address, value),
        run: (frames) => {
            elapsed += frames;
            for (let i = 0; i < frames; i++) machine.videoClockPulse();
        },
        xy: () => [word(0xf100), word(0xf102)],
        currentView: () => Buffer.from(Array.from({ length: 512 }, (_, i) => read(viewStart + i))),
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
    assert.equal(regs[2], run.read(0xf105), "R2 deve apontar para a página apresentada.");
    const base = regs[2] << 10;
    const frame = Buffer.from(Array.from({ length: 24 * 32 }, (_, i) => run.read(frameStart + i)));
    assert.deepEqual(vram.subarray(base, base + frame.length), frame);
}

function checkTitleArt(demo) {
    // The CPU may be halfway through uploading tiles on a phase boundary.
    if ((demo.read(0xf12c) & 7) === 0) demo.run(1);
    const { regs, vram } = demo.video();
    const base = regs[2] << 10;
    assert.deepEqual(vram.subarray(base, base + titlePicture.length), titlePicture);
    const motionSize = romAddress("title_motion_1") - romAddress("title_motion_0");
    const phase = demo.read(state.titlePhase);
    const motion = romTiles(`title_motion_${phase}`, motionSize);
    for (let bank = 0; bank < 2; bank++) {
        const patterns = `title_patterns_${bank}`;
        const colors = `title_colors_${bank}`;
        const size = romAddress(colors) - romAddress(patterns);
        const offset = bank * 0x800;
        const expectedPatterns = Buffer.from(romTiles(patterns, size));
        const expectedColors = Buffer.from(romTiles(colors, size));
        for (let i = 0; i < motion.length; i += 18) {
            if (motion[i + 1] !== bank * 8) continue;
            const tile = motion[i] * 8;
            motion.copy(expectedPatterns, tile, i + 2, i + 10);
            motion.copy(expectedColors, tile, i + 10, i + 18);
        }
        assert.deepEqual(vram.subarray(offset, offset + size), expectedPatterns);
        assert.deepEqual(vram.subarray(0x2000 + offset, 0x2000 + offset + size), expectedColors);
    }
}

const state = {
    playerX: 0xf100, playerY: 0xf102, heading: 0xf104, page: 0xf105, shown: 0xf10b, life: 0xf10f,
    ammo: 0xf110, enemyEnd: 0xf111, propEnd: 0xf112, keysHeld: 0xf113, mapTop: 0xf116,
    outcome: 0xf119, hint: 0xf11a, flash: 0xf11b, menu: 0xf125, sector: 0xf126, weapon: 0xf12a, minimap: 0xf127,
    difficulty: 0xf145, sight: 0xf147, attackDelay: 0xf148, chaseDelay: 0xf149, seed: 0xf14a,
    titlePhase: 0xf150,
    musicEnabled: 0xf151, musicPhase: 0xf154, musicLoop: 0xf156, musicNext: 0xf158, musicB: 0xf15a, musicC: 0xf15c,
    eventTimer: 0xf128,
    wallDepth: 0xf160, enemies: 0xc420, props: 0xc520, map: 0xc400,
};
const up = 0x20;
const down = 0x40;
const right = 0x80;
const space = 1;
const width = 32;
const height = 44;
const sectorStarts = [[4, 40], [27, 8], [4, 40]];
const initialCharges = [8, 9, 10];
const enemyCounts = [11, 12, 13];
const names = ["Depósito", "Fundição", "Reator"];

function mapAddress(x, y) {
    return state.map + y * 256 + x;
}

function entities(demo, base, end) {
    const list = [];
    for (let address = base; (address & 255) !== demo.read(end); address += 8) {
        list.push({
            address,
            x: demo.read(address + 2),
            y: demo.read(address + 4),
            kind: demo.read(address + 6),
            arg: demo.read(address + 7),
        });
    }
    return list;
}

function placePlayer(demo, x, y, heading = 0) {
    for (const [axis, coordinate] of [[state.playerX, x], [state.playerY, y]]) {
        demo.write(axis, 128);
        demo.write(axis + 1, coordinate);
    }
    demo.write(state.heading, heading);
}

function installEntities(demo, base, end, records) {
    for (const [i, [x, y, kind, arg, wait = 0]] of records.entries()) {
        const bytes = [base === state.enemies ? arg : 1, 128, x, 128, y, wait, kind, arg];
        bytes.forEach((value, offset) => demo.write(base + i * 8 + offset, value));
    }
    demo.write(end, (base + records.length * 8) & 255);
}

function emptyRoom(demo) {
    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            demo.write(mapAddress(x, y), x > 0 && x < 15 && y > 0 && y < 15 ? 0 : 1);
        }
    }
    installEntities(demo, state.enemies, state.enemyEnd, [[25, 25, 0, 2]]);
    installEntities(demo, state.props, state.propEnd, [[25, 25, 0, 6]]);
}

function creatureTileCount(demo) {
    const { regs, vram } = demo.video();
    const start = (regs[2] << 10) + 128;
    return vram.subarray(start, start + 512).filter((tile) => creatureTiles.has(tile)).length;
}

function mapTile(demo, x, y) {
    return demo.currentView()[(y - demo.read(state.mapTop)) * width + x];
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

function startCampaign(frequency, difficulty = 1, delay = 0) {
    const demo = boot(frequency);
    demo.run(180 + delay);
    assert.equal(demo.read(state.outcome), 4, "O cartucho deve iniciar na tela de título.");
    assert.equal(demo.read(state.difficulty), 1);
    if (difficulty === 0) press(demo, "keys", 0x10);
    if (difficulty === 2) press(demo, "stick", 0x08);
    assert.equal(demo.read(state.difficulty), difficulty);
    const selection = Buffer.from(Array.from({ length: 8 }, (_, i) =>
        demo.read(viewStart + titleDifficultyOffset + i)));
    assert.deepEqual(selection, difficultyNames.subarray(difficulty * 8, difficulty * 8 + 8));
    checkTitleArt(demo);
    checkVideo(demo);
    press(demo, "keys", space);
    assert.equal(demo.read(state.outcome), 0);
    return demo;
}

function checkWallEdges(frequency, material, direction) {
    const demo = startCampaign(frequency);
    emptyRoom(demo);
    demo.write(state.minimap, 0);
    const rotate = (x, y) => direction === 0 ? [x, y] : [15 - y, x];
    for (let y = 1; y < 15; y++) {
        for (let x = 1; x < 15; x++) {
            const [column, row] = rotate(x, y);
            // One block in front of a continuous wall of the same stone.
            const wall = y === 7 || (y === 10 && x === 5);
            demo.write(mapAddress(column, row), wall ? material : 0);
        }
    }
    const [x, y] = rotate(5, 12);
    placePlayer(demo, x, y, direction);
    press(demo, "menu", true);
    press(demo, "menu", true);
    checkVideo(demo);

    const depths = Array.from({ length: 32 }, (_, i) => demo.read(state.wallDepth + i));
    const nearest = Math.min(...depths);
    const left = depths.indexOf(nearest);
    const right = depths.lastIndexOf(nearest);
    assert.ok(left > 0 && right < 31 && right - left > 1);
    const styles = romTiles("wall_styles", 8);
    const heights = romTiles("heights", romAddress("slope_sizes") - romAddress("heights"));
    const view = demo.currentView();
    for (const [column, depth] of depths.entries()) {
        const edge = column === left || column === right;
        const style = material + (edge ? 4 : 0);
        const tile = demo.read(mapAddress(styles[style] + 7, heights[depth] + 2));
        assert.equal(view[7 * 32 + column], tile, `Borda indevida ou ausente na coluna ${column}.`);
    }
}

function checkSlopedWall(frequency, material) {
    const demo = startCampaign(frequency);
    emptyRoom(demo);
    demo.write(state.minimap, 0);
    for (let x = 1; x < 15; x++) demo.write(mapAddress(x, 7), material);
    const heights = romTiles("heights", romAddress("slope_sizes") - romAddress("heights"));
    const sizes = romTiles("slope_sizes", romAddress("slope_profiles") - romAddress("slope_sizes"));
    const profiles = new Map([[0x07, 0x3f], [0xe0, 0xfc], [0x03, 0x0f], [0xc0, 0xf0]]);
    const observed = new Set();
    const highlight = material === 1 ? 5 : 10;
    const shade = material === 1 ? 4 : 6;

    for (const [x, y, heading] of [[8, 10, 7], [7, 8, 52]]) {
        placePlayer(demo, x, y, heading);
        press(demo, "menu", true);
        press(demo, "menu", true);
        const { vram } = demo.video();
        const view = demo.currentView();
        for (let column = 0; column < width; column++) {
            const size = sizes[heights[demo.read(state.wallDepth + column)]];
            if (size === 64) continue;
            const top = 64 - size;
            const row = top >> 3;
            const clip = top & 7;
            const cap = ((row + 4) >> 3) * 0x800 + view[row * width + column] * 8;
            if (vram[0x2000 + cap + clip] !== (highlight << 4)) continue;
            const first = vram[cap + clip];
            assert.equal(vram[cap + clip + 1], profiles.get(first));
            const bottomRow = 15 - row;
            const foot = ((bottomRow + 4) >> 3) * 0x800 + view[bottomRow * width + column] * 8;
            assert.equal(vram[foot + 7 - clip], first);
            assert.equal(vram[foot + 6 - clip], profiles.get(first));
            assert.equal(vram[0x2000 + foot + 7 - clip], shade << 4);
            observed.add(first);
        }
    }
    assert.ok(observed.has(0xe0) && observed.has(0x03), "A parede deve suavizar inclinações nos dois sentidos.");

    placePlayer(demo, 8, 11);
    press(demo, "menu", true);
    press(demo, "menu", true);
    const depth = demo.read(state.wallDepth + 16);
    assert.equal(sizes[heights[depth]], 18, "A parede distante deve ter 36 pixels de altura.");

    placePlayer(demo, 8, 8);
    demo.write(state.playerY, 192);
    press(demo, "menu", true);
    press(demo, "menu", true);
    const extendedWall = demo.currentView()[16];
    for (const row of [2, 3, 20, 21]) {
        assert.equal(demo.read(frameStart + row * width + 16), extendedWall);
    }
    for (const row of [1, 22]) {
        assert.notEqual(demo.read(frameStart + row * width + 16), extendedWall);
    }

    placePlayer(demo, 8, 8);
    demo.write(state.playerY, 64);
    press(demo, "menu", true);
    press(demo, "menu", true);
    const nearWall = demo.currentView()[16];
    for (const row of [0, 1, 2, 3, 20, 21, 22]) {
        assert.equal(demo.read(frameStart + row * width + 16), nearWall, "A parede próxima deve preencher a área ampliada.");
    }
    checkVideo(demo);
}

function holdUntil(demo, keys, condition, limit = 500, settle = 12) {
    demo.inputs.keys = keys;
    for (let i = 0; i < limit && !condition(); i++) demo.run(1);
    assert.ok(condition(), "A ação deve chegar ao estado esperado.");
    demo.inputs.keys = 0;
    demo.run(settle);
}

function checkHealthHud(demo, full) {
    const { regs, vram } = demo.video();
    const firstSlot = (regs[2] << 10) + hudRow * 32 + lifeOffset;
    const expected = Buffer.from(Array.from({ length: 5 }, (_, i) => i < full ? heartFull : heartEmpty));
    assert.deepEqual(vram.subarray(firstSlot, firstSlot + 5), expected, "O HUD deve exibir os corações restantes.");
}

function redViewportPixels(frame) {
    const pixels = frame.image.data;
    let red = 0;
    for (let y = 44; y < 156; y++) {
        for (let x = 16; x < 256; x++) {
            const source = (y * frame.image.width + x) * 4;
            if (pixels[source] > pixels[source + 1] + 45 && pixels[source] > pixels[source + 2] + 45) red++;
        }
    }
    return red;
}

function checkDamageFeedback(demo, frequency) {
    const baseline = demo.video().regs[7];
    const psg = () => Buffer.from(demo.machine.psg.saveState().r, "base64");
    const initialRed = redViewportPixels(demo.frame);
    demo.inputs.keys = up;
    for (let i = 0; i < 500 && demo.read(state.life) === 5; i++) demo.run(1);
    demo.inputs.keys = 0;
    assert.equal(demo.read(state.life), 4);
    assert.equal(demo.video().regs[7] & 0x0f, 9);
    assert.equal(psg()[4], 126);
    assert.equal(psg()[10], 12);

    demo.inputs.keys = space;
    let flashVisible = false;
    let lowerTone = false;
    let mixedShot = false;
    let darkRedSeen = false;
    for (let i = 0; i < 13; i++) {
        demo.run(1);
        const registers = psg();
        const video = demo.video();
        lowerTone ||= registers[4] === 224 && registers[10] === 12;
        mixedShot ||= registers[8] > 0 && registers[10] === 12 && (registers[7] & 0x0c) === 0;
        darkRedSeen ||= (video.regs[7] & 0x0f) === 6;
        if (redViewportPixels(demo.frame) > initialRed + 4000) {
            flashVisible = true;
            if (frequency === 60 && damagePath && i === 6) saveFrame(demo.frame, damagePath);
        }
    }
    demo.inputs.keys = 0;
    assert.ok(flashVisible && darkRedSeen, "O clarão deve aparecer no cenário e escurecer antes de sumir.");
    assert.ok(lowerTone && mixedShot, "O som de dano deve descer e tocar junto com o disparo.");
    assert.equal(demo.video().regs[7], baseline);
    checkMusicVoice(demo, 2);
    checkHealthHud(demo, 4);
}

function capturePsg(demo, frames, frequency) {
    let signal;
    demo.machine.getAudioSocket().connectMonitor({
        connectAudioSignal(source) {
            signal = source;
            source.setAudioMonitorBufferSize(4096);
        },
    });
    const rate = signal.getSampleRate();
    const pcmRate = Math.round(rate / 2);
    const pcm = Buffer.alloc(Math.ceil(frames * pcmRate / frequency) * 2);
    let samplesRead = 0;
    let next = 0;
    let first = 0;
    let peak = 0;
    return {
        readFrame() {
            const end = Math.floor((next += rate) / frequency);
            const size = end - samplesRead;
            const data = signal.retrieveSamples(size, false);
            for (let i = 0; i < size; i++, samplesRead++) {
                const sample = data.buffer0[(data.start + i) % data.bufferSize];
                if ((samplesRead & 1) === 0) {
                    first = sample;
                } else {
                    const value = Math.max(-1, Math.min(1, (first + sample) / 2));
                    peak = Math.max(peak, Math.abs(value));
                    pcm.writeInt16LE(Math.round(value * 32767), samplesRead - 1);
                }
            }
        },
        save(filename) {
            assert.ok(peak > 0.05, "A gravação do PSG deve conter áudio.");
            const length = samplesRead & ~1;
            const header = Buffer.alloc(44);
            header.write("RIFF", 0);
            header.writeUInt32LE(36 + length, 4);
            header.write("WAVEfmt ", 8);
            header.writeUInt32LE(16, 16);
            header.writeUInt16LE(1, 20);
            header.writeUInt16LE(1, 22);
            header.writeUInt32LE(pcmRate, 24);
            header.writeUInt32LE(pcmRate * 2, 28);
            header.writeUInt16LE(2, 32);
            header.writeUInt16LE(16, 34);
            header.write("data", 36);
            header.writeUInt32LE(length, 40);
            writeFileSync(filename, Buffer.concat([header, pcm.subarray(0, length)]));
        },
    };
}

function checkOpening(frequency) {
    const demo = boot(frequency);
    const word = (address) => demo.read(address) | (demo.read(address + 1) << 8);
    const order = romAddress("intro_order");
    const first = romTiles("intro_order", 2).readUInt16LE();
    const frames = 16 * 14 * frequency / 10;
    const psg = () => Buffer.from(demo.machine.psg.saveState().r, "base64");
    for (let i = 0; i < 360 && demo.read(state.outcome) !== 4; i++) demo.run(1);
    assert.equal(demo.read(state.outcome), 4);
    demo.run(1); // Sample after the initial name-table upload.
    assert.equal(demo.read(0xf12d), frequency === 60 ? 5 : 6);
    assert.equal(word(0xf130), order + 2);
    assert.equal(word(0xf132), first + 4);
    const firstMeter = demo.currentView().subarray(titleMeterOffset, titleMeterOffset + 24);
    let meterChanged = false;
    let notes = 0;
    let previousStep = word(0xf132);
    let heardAllChannels = false;
    const noisePeriods = new Set();
    const mixerIO = psg()[7] & 0xc0;
    const recorder = frequency === 60 && openingPath ? capturePsg(demo, frames, frequency) : null;
    for (let i = 0; i < frames; i++) {
        demo.run(1);
        if (recorder) recorder.readFrame();
        const step = word(0xf132);
        if (step !== previousStep) notes++;
        previousStep = step;
        const registers = psg();
        heardAllChannels ||= registers[8] > 0 && registers[9] > 0 && registers[10] > 0;
        if ((registers[7] & 0x20) === 0) noisePeriods.add(registers[6]);
        assert.equal(registers[7] & 0xc0, mixerIO);
        const meter = demo.currentView().subarray(titleMeterOffset, titleMeterOffset + 24);
        meterChanged ||= !firstMeter.equals(meter);
        if (i === frequency && frequency === 60 && titlePath) saveFrame(demo.frame, titlePath);
    }
    assert.equal(notes, 224, "A abertura deve completar o mesmo ciclo de 22,4 s em 50 e 60 Hz.");
    assert.equal(word(0xf130), order + 2, "A faixa deve voltar ao primeiro compasso.");
    assert.equal(word(0xf132), first + 4);
    assert.ok(heardAllChannels && noisePeriods.size > 2 && meterChanged);
    if (recorder) recorder.save(openingPath);
    checkTitleArt(demo);
    const scorePosition = word(0xf132);

    press(demo, "keys", space);
    assert.equal(demo.read(state.outcome), 0);
    assert.equal(psg()[8], 0, "A trilha deve reservar o canal A para os disparos.");
    assert.ok(psg()[9] || psg()[10], "A música do setor deve começar ao jogar.");
    assert.equal(psg()[7] & 0x3f, 0x31);
    assert.equal(word(0xf132), scorePosition, "O leitor da faixa deve ficar parado durante a partida.");
    checkWeapon(demo, 0);
    checkVideo(demo);
    console.log(`Abertura em ${frequency} Hz: 224 passos em 22,4 s, três canais e ruído ativos, repetição e mute OK.`);
}

function face(demo, angle, settle = 12) {
    const distance = (angle - demo.read(state.heading) + 64) & 63;
    if (distance === 0) return;
    holdUntil(demo, distance <= 32 ? right : 0x10, () => demo.read(state.heading) === angle, 500, settle);
}

function checkWeapon(demo, index) {
    assert.equal(demo.read(state.weapon), index);
    const { regs, vram } = demo.video();
    const name = (regs[2] << 10) + hudRow * 32 + weaponOffset;
    assert.deepEqual(vram.subarray(name, name + 7), weaponNames.subarray(index * 7, index * 7 + 7));
    assert.equal(vram[0x1b0a], index === 0 ? 1 : 8);
}

function checkSector(demo, index, difficulty = 1) {
    assert.equal(demo.read(state.sector), index);
    assert.equal(demo.read(state.outcome), 0);
    assert.deepEqual(demo.xy(), sectorStarts[index].map((axis) => axis * 256 + 128));
    assert.equal(demo.read(state.ammo), initialCharges[index]);
    assert.equal(demo.read(state.life), 5);
    assert.equal(demo.read(state.keysHeld), 0);
    assert.equal(demo.read(state.difficulty), difficulty);
    assert.equal(entities(demo, state.enemies, state.enemyEnd).length, enemyCounts[index] + 3 * (difficulty - 1));
    const props = entities(demo, state.props, state.propEnd);
    for (const gate of props.filter(({ kind }) => kind === 3)) {
        assert.equal(demo.read(gate.address), 1);
        assert.equal(demo.read(mapAddress(gate.x, gate.y)), 3);
    }
    checkWeapon(demo, 0);
    checkHealthHud(demo, 5);
    const { regs, vram } = demo.video();
    assert.equal(vram[(regs[2] << 10) + hudRow * 32 + sectorOffset], digitTiles[index + 1]);
    checkVideo(demo);
}

function checkPlacement(demo) {
    const enemies = entities(demo, state.enemies, state.enemyEnd);
    const props = entities(demo, state.props, state.propEnd);
    const toCell = ({ x, y }) => y * width + x;
    const terrain = Array.from({ length: width * height }, (_, cell) =>
        demo.read(mapAddress(cell % width, Math.floor(cell / width))));
    assert.ok(terrain.every((tile) => tile <= 3), "O sorteio deve limpar todas as reservas do terreno.");
    const [x, y] = demo.xy().map((coordinate) => coordinate >> 8);
    const start = toCell({ x, y });
    const occupied = new Set([start]);
    for (const entity of [...enemies, ...props]) {
        const cell = toCell(entity);
        assert.ok(!occupied.has(cell), "Entidades não devem compartilhar uma célula inicial.");
        assert.equal(terrain[cell], props.includes(entity) && entity.kind === 3 ? 3 : 0);
        occupied.add(cell);
    }

    const keys = props.filter(({ kind }) => kind === 2).sort((a, b) => a.arg - b.arg);
    const gates = props.filter(({ kind }) => kind === 3).sort((a, b) => a.arg - b.arg);
    const exit = toCell(props.find(({ kind }) => kind === 4));
    for (const [index, key] of keys.entries()) {
        const path = [start];
        const seen = new Set(path);
        for (let i = 0; i < path.length; i++) {
            const current = path[i];
            for (const next of [current - width, current + 1, current + width, current - 1]) {
                if (terrain[next] !== 0 || seen.has(next)) continue;
                seen.add(next);
                path.push(next);
            }
        }
        assert.ok(seen.has(toCell(key)), "A próxima chave deve estar na área acessível.");
        for (const later of keys.slice(index + 1)) assert.ok(!seen.has(toCell(later)));
        assert.ok(!seen.has(exit), "A sequência de portões deve proteger a saída.");
        terrain[toCell(gates[index])] = 0;
    }
    return [enemies, ...[0, 1, 2].map((kind) => props.filter((prop) => prop.kind === kind))]
        .map((group) => group.map(toCell));
}

function checkDifficulty(frequency) {
    const normal = startCampaign(frequency);
    const positions = checkPlacement(normal);
    const nextRun = startCampaign(frequency, 1, 29);
    const nextPositions = checkPlacement(nextRun);
    for (const [kind, group] of positions.entries()) {
        assert.notDeepEqual(nextPositions[kind], group, "Uma nova semente deve variar inimigos, munição, cura e chaves.");
    }
    const seed = [normal.read(state.seed), normal.read(state.seed + 1)];
    assert.notDeepEqual([nextRun.read(state.seed), nextRun.read(state.seed + 1)], seed);
    press(normal, "retry", true);
    assert.deepEqual([normal.read(state.seed), normal.read(state.seed + 1)], seed);
    assert.deepEqual(checkPlacement(normal), positions, "Reiniciar deve conservar a distribuição do setor.");

    for (const [difficulty, sight, attack, chase] of [[0, 3, 14, 2], [1, 4, 10, 1], [2, 5, 6, 0]]) {
        const demo = difficulty === 1 ? normal : startCampaign(frequency, difficulty);
        checkSector(demo, 0, difficulty);
        checkPlacement(demo);
        assert.deepEqual([state.sight, state.attackDelay, state.chaseDelay].map(demo.read), [sight, attack, chase]);
        emptyRoom(demo);
        placePlayer(demo, 5, 12);
        installEntities(demo, state.enemies, state.enemyEnd, [[5, 8, 0, 2]]);
        demo.run(20);
        const enemyY = demo.read(state.enemies + 3) + 256 * demo.read(state.enemies + 4);
        assert.equal(enemyY > 8 * 256 + 128, difficulty === 2, "Difícil deve detectar o jogador de mais longe.");
        installEntities(demo, state.enemies, state.enemyEnd, [[5, 12, 0, 2]]);
        demo.write(state.enemies + 3, 48);
        for (let i = 0; i < 30 && demo.read(state.life) === 5; i++) demo.run(1);
        assert.equal(demo.read(state.life), 4);
        assert.equal(demo.read(state.enemies + 5), attack, "A dificuldade deve mudar o intervalo entre ataques.");
    }
}

function checkMenu(demo, frequency) {
    press(demo, "menu", true);
    assert.equal(demo.read(state.menu), 2, "A pausa deve abrir no mapa.");
    assert.equal(demo.video().vram[0x1b00], 208);
    const frozen = demo.xy();
    checkPlayerMarker(demo);
    const origin = demo.read(state.mapTop);
    press(demo, "keys", up);
    assert.ok(demo.read(state.mapTop) < origin, "A aba de mapa deve permitir olhar para o norte.");
    assert.deepEqual(demo.xy(), frozen);
    press(demo, "keys", down);
    assert.equal(demo.read(state.mapTop), origin);
    if (frequency === 60 && mapPath) saveFrame(demo.frame, mapPath);

    press(demo, "stick", 0x08);
    assert.equal(demo.read(state.menu), 1);
    const legend = demo.currentView();
    for (const [index, tile] of terrain.entries()) assert.equal(legend[(5 + 2 * index) * 32 + 2], tile);
    for (const [index, tile] of [playerArrows[0], ...visibleObjects].entries()) {
        assert.equal(legend[(5 + 2 * index) * 32 + 20], tile);
    }
    assert.equal(legend[15 * 32 + 2], heartFull);
    if (frequency === 60 && legendPath) saveFrame(demo.frame, legendPath);

    press(demo, "keys", 0x10);
    assert.equal(demo.read(state.menu), 2);
    checkPlayerMarker(demo);
    press(demo, "stick", 0x30);
    assert.equal(demo.read(state.menu), 0);
    assert.equal(demo.read(state.ammo), 8, "Abrir ou fechar o menu não deve disparar.");
    checkVideo(demo);
}

function checkMinimap(frequency) {
    const demo = startCampaign(frequency);
    assert.equal(demo.read(state.minimap), 1);
    emptyRoom(demo);
    const doors = [[5, 11, 3, 1], [6, 12, 0, 8], [6, 13, 2, 2]];
    installEntities(demo, state.props, state.propEnd, doors);
    installEntities(demo, state.enemies, state.enemyEnd, [[7, 11, 0, 2]]);
    demo.write(state.enemies + 5, 255); // Keep the living enemy still in the fixture.
    demo.write(mapAddress(4, 10), 1);
    demo.write(mapAddress(8, 10), 2);
    demo.write(mapAddress(5, 11), 3);
    placePlayer(demo, 5, 12);

    const syncView = () => {
        press(demo, "menu", true);
        press(demo, "menu", true);
    };
    const checkTerrain = (arrow) => {
        const [x, y] = demo.xy().map((coordinate) => coordinate >> 8);
        const left = Math.max(0, Math.min(width - 7, x - 3));
        const top = Math.max(0, Math.min(height - 5, y - 2));
        const { regs, vram } = demo.video();
        const base = (regs[2] << 10) + 32 + 24;
        for (let row = 0; row < 5; row++) {
            for (let col = 0; col < 7; col++) {
                const mapX = left + col, mapY = top + row;
                const expected = mapX === x && mapY === y ? playerArrows[arrow]
                    : miniTerrain[demo.read(mapAddress(mapX, mapY))];
                assert.equal(vram[base + row * 32 + col], expected, "Minimapa deve mostrar apenas terreno e jogador.");
            }
        }
    };
    syncView();
    checkTerrain(0);
    press(demo, "menu", true);
    assert.equal(mapTile(demo, 7, 11), visibleObjects[0]);
    assert.equal(mapTile(demo, 6, 12), visibleObjects[1]);
    assert.equal(mapTile(demo, 6, 13), visibleObjects[4]);
    press(demo, "menu", true);

    demo.inputs.minimap = true;
    demo.run(40);
    demo.inputs.minimap = false;
    demo.run(12);
    assert.equal(demo.read(state.minimap), 0, "N deve alternar somente uma vez enquanto estiver pressionado.");
    assert.notEqual(demo.read(frameStart + 3 * 32 + 27), playerArrows[0]);
    const before = demo.xy();
    press(demo, "stick", 0x22); // B + down
    assert.equal(demo.read(state.minimap), 1);
    assert.deepEqual(demo.xy(), before, "O atalho do joystick não deve mover o jogador.");
    face(demo, 16);
    checkTerrain(1);
    face(demo, 0);
    demo.write(state.keysHeld, 1);
    holdUntil(demo, up, () => demo.xy()[1] < before[1]);
    press(demo, "shift", true);
    assert.equal(demo.read(mapAddress(5, 11)), 0);
    checkTerrain(0);
    walkRun(demo, [5, 11], 0);
    checkTerrain(0);
    placePlayer(demo, 1, 2);
    syncView();
    checkTerrain(0);
    checkVideo(demo);
}

// Isolate gun range, enemy movement, damage effects and supplies from the
// layout of the campaign. The campaign navigation below uses the shipped maps.
function openArena(frequency, enemies, props = [[11, 10, 0, 6]]) {
    const demo = startCampaign(frequency);
    emptyRoom(demo);
    installEntities(demo, state.enemies, state.enemyEnd, enemies);
    installEntities(demo, state.props, state.propEnd, props);
    placePlayer(demo, 5, 12);
    press(demo, "menu", true);
    press(demo, "menu", true);
    return demo;
}

function wordAt(demo, address) {
    return demo.read(address) | demo.read(address + 1) << 8;
}

function psgRegisters(demo) {
    return Buffer.from(demo.machine.psg.saveState().r, "base64");
}

function checkMusicVoice(demo, channel) {
    const sound = wordAt(demo, channel === 1 ? state.musicB : state.musicC);
    const psg = psgRegisters(demo);
    const gain = demo.read(state.musicEnabled) ? sound >> 12 : 0;
    assert.equal(psg[8 + channel], gain, "O canal deve voltar à trilha após o efeito.");
    if (gain) assert.equal(psg.readUInt16LE(channel * 2), sound & 0xfff);
}

function checkMusicControls(frequency) {
    const demo = openArena(frequency, [[12, 12, 0, 2]], [[5, 11, 0, 6]]);
    assert.equal(demo.read(state.musicEnabled), 1);
    const before = wordAt(demo, state.musicNext);
    press(demo, "music", true);
    assert.equal(demo.read(state.musicEnabled), 0);
    assert.equal(demo.read(state.hint), 8);
    checkMusicVoice(demo, 1);
    checkMusicVoice(demo, 2);
    assert.notEqual(wordAt(demo, state.musicNext), before, "A faixa deve avançar mesmo silenciada.");

    const position = demo.xy();
    const heading = demo.read(state.heading);
    press(demo, "stick", 0x28); // B + right
    assert.equal(demo.read(state.musicEnabled), 1);
    assert.equal(demo.read(state.hint), 7);
    assert.equal(demo.read(state.heading), heading);
    assert.deepEqual(demo.xy(), position);
    checkMusicVoice(demo, 1);
    checkMusicVoice(demo, 2);

    demo.inputs.keys = up;
    for (let i = 0; i < 180 && !demo.read(state.eventTimer); i++) demo.run(1);
    demo.inputs.keys = 0;
    assert.ok(demo.read(state.eventTimer), "A caixa deve tocar sua indicação sonora.");
    assert.equal(psgRegisters(demo)[2], 110);
    assert.equal(psgRegisters(demo)[9], 9);
    demo.run(20);
    assert.equal(demo.read(state.eventTimer), 0);
    checkMusicVoice(demo, 1);

    press(demo, "menu", true);
    press(demo, "stick", 0x28);
    assert.equal(demo.read(state.menu), 2, "Alternar a música não deve trocar a aba do mapa.");
    assert.equal(demo.read(state.musicEnabled), 0);
    press(demo, "menu", true);
    press(demo, "retry", true);
    assert.equal(demo.read(state.musicEnabled), 0, "Reiniciar deve conservar a preferência de áudio.");
    checkMusicVoice(demo, 1);
    checkMusicVoice(demo, 2);
}

function checkTrack(demo, sector, frequency) {
    const start = romAddress(`game_music_${sector}`);
    const end = romAddress(sector === 2 ? "rom_end" : `game_music_${sector + 1}`);
    const interval = romTiles("game_music_tracks", 9)[sector * 3 + 2];
    const frames = (end - start - 2) / 4;
    assert.equal(wordAt(demo, state.musicLoop), start);
    press(demo, "menu", true);
    let previous = wordAt(demo, state.musicNext);
    const played = (previous - start) / 4 - 1;
    const expected = ((frames - played) * interval - demo.read(state.musicPhase)) * frequency / 300;
    const pitches = [new Set(), new Set()];
    let elapsed = 0;
    for (; elapsed < Math.ceil(expected) + 6; elapsed++) {
        demo.run(1);
        const current = wordAt(demo, state.musicNext);
        if (current === previous) continue;
        if (current < previous) break;
        previous = current;
        const psg = psgRegisters(demo);
        for (let channel = 1; channel <= 2; channel++) {
            if (psg[8 + channel]) pitches[channel - 1].add(psg.readUInt16LE(channel * 2));
        }
    }
    assert.equal(wordAt(demo, state.musicNext), start + 4, "A faixa deve voltar ao primeiro quadro.");
    assert.ok(Math.abs(elapsed + 1 - expected) < 3, "O loop deve respeitar o tempo nos dois padrões de vídeo.");
    assert.ok(pitches.every((voice) => voice.size >= 5), "Melodia e baixo devem apresentar notas variadas.");
    press(demo, "menu", true);
}

function checkArena(frequency) {
    const demo = openArena(frequency, [[5, 8, 0, 2], [11, 8, 1, 4]], [[6, 12, 0, 6], [7, 12, 1, 2]]);
    assert.ok(creatureTileCount(demo) > 0);
    press(demo, "weapon", true);
    checkWeapon(demo, 1);
    press(demo, "keys", space);
    assert.equal(demo.read(state.enemies), 2, "Pistola de pulso fora do alcance.");
    assert.equal(demo.read(state.ammo), 6);
    press(demo, "weapon", true);
    checkWeapon(demo, 0);
    press(demo, "keys", space);
    assert.equal(demo.read(state.enemies), 1);
    press(demo, "stick", 0x10);
    assert.equal(demo.read(state.enemies), 0);
    assert.equal(demo.read(state.ammo), 4);
    assert.equal(demo.read(state.enemies + 8), 4);

    // Approach the box and the medkit with walking input.
    face(demo, 16);
    demo.write(state.life, 2);
    walkRun(demo, [7, 12], 16);
    demo.run(12);
    assert.equal(demo.read(state.ammo), 10);
    assert.equal(demo.read(state.life), 4);
    assert.equal(demo.read(state.props), 0);
    assert.equal(demo.read(state.props + 8), 0);
    assert.equal(demo.read(hudStart + ammoOffset), digitTiles[1]);
    assert.equal(demo.read(hudStart + ammoOffset + 1), digitTiles[0]);
    checkHealthHud(demo, 4);

    const two = openArena(frequency, [[4, 9, 0, 2, 255], [6, 9, 1, 4, 255]]);
    const view = two.currentView();
    assert.ok(view.some((tile) => creatureTiles.has(tile)) && view.some((tile) => bruteTiles.has(tile)),
        "As duas espécies devem aparecer juntas.");

    const pulse = openArena(frequency, [[5, 9, 1, 4]]);
    press(pulse, "weapon", true);
    pulse.inputs.keys = space;
    pulse.run(frequency);
    pulse.inputs.keys = 0;
    assert.equal(pulse.read(state.enemies), 0, "Rajadas de pulso devem derrubar um bruto.");
    assert.ok(pulse.read(state.ammo) <= 4, "O tiro deve repetir com o gatilho pressionado.");

    const blocked = openArena(frequency, [[5, 8, 0, 2]], [[5, 10, 3, 1], [6, 12, 2, 2]]);
    for (let x = 1; x < 15; x++) blocked.write(mapAddress(x, 10), x === 5 ? 3 : 1);
    face(blocked, 16);
    walkRun(blocked, [6, 12], 16);
    blocked.run(12);
    assert.equal(blocked.read(state.keysHeld), 2);
    face(blocked, 48);
    walkRun(blocked, [5, 12], 48);
    face(blocked, 0);
    holdUntil(blocked, up, () => blocked.xy()[1] < 11 * 256 + 80);
    press(blocked, "shift", true);
    assert.equal(blocked.read(state.props), 1);
    assert.equal(blocked.read(state.hint), 5, "Uma chave de outra porta não pode abrir o portão.");
    assert.equal(creatureTileCount(blocked), 0);
    press(blocked, "keys", space);
    assert.equal(blocked.read(state.enemies), 2, "A porta deve barrar o disparo e a criatura.");
    assert.equal(blocked.read(state.enemies + 3), 128);
    checkVideo(blocked);

    const damage = openArena(frequency, [[5, 8, 0, 2]]);
    if (frequency === 50) press(damage, "music", true);
    checkDamageFeedback(damage, frequency);
    if (frequency === 60 && healthPath) saveFrame(damage.frame, healthPath);
    holdUntil(damage, up, () => damage.read(state.outcome) === 1, 1000);
    checkHealthHud(damage, 0);
    press(damage, "stick", 0x10);
    checkSector(damage, 0);

    const combat = openArena(frequency, [[5, 8, 0, 2]]);
    const before = combat.read(state.shown);
    const farTiles = creatureTileCount(combat);
    combat.inputs.keys = up;
    combat.run(frequency);
    combat.inputs.keys = 0;
    const frames = (combat.read(state.shown) - before + 256) % 256;
    let nearTiles = 0;
    for (let i = 0; i < 10; i++) {
        combat.run(1);
        nearTiles = Math.max(nearTiles, creatureTileCount(combat));
    }
    assert.ok(nearTiles > farTiles, "O monstro deve crescer ao se aproximar.");
    combat.inputs.keys = space;
    let flash = false;
    for (let i = 0; i < 20; i++) {
        combat.run(1);
        if (combat.read(state.enemies) === 1) combat.inputs.keys = 0;
        if (combat.video().vram[0x1b04] === 159 && creatureTileCount(combat) > farTiles && !flash) {
            flash = true;
            if (frequency === 60 && snapshotPath) {
                combat.run(1);
                saveFrame(combat.frame, snapshotPath);
            }
        }
    }
    assert.ok(flash);
    assert.equal(combat.read(state.enemies), 1);
    assert.ok(frames >= 10, `Combate isolado a ${frequency} Hz: ${frames} quadros/s.`);
    console.log(`Combate isolado a ${frequency} Hz: ${frames} quadros no primeiro segundo.`);
}

// Plan from the live terrain, then send only directional controls to walk it.
function routeTo(demo, target, includeDoor) {
    const cell = (x, y) => y * width + x;
    const [x, y] = demo.xy().map((axis) => axis >> 8);
    const start = cell(x, y);
    const end = cell(target.x, target.y);
    const parents = new Map([[start, start]]);
    const todo = [start];
    for (let i = 0; i < todo.length && !parents.has(end); i++) {
        const current = todo[i];
        for (const next of [current - width, current + 1, current + width, current - 1]) {
            if (parents.has(next)) continue;
            if (demo.read(mapAddress(next % width, Math.floor(next / width))) && !(includeDoor && next === end)) {
                continue;
            }
            parents.set(next, current);
            todo.push(next);
        }
    }
    assert.ok(parents.has(end), `Sem rota para ${target.x},${target.y}.`);
    const path = [];
    for (let next = end; next !== start; next = parents.get(next)) path.push(next);
    return [start, ...path.reverse()];
}

function walkRun(demo, target, heading, exit = false, settle = 12) {
    const axis = heading % 32 ? 0 : 1;
    const increasing = heading === 16 || heading === 32;
    const goal = target[axis] * 256 + 128;
    const reached = () => {
        if (exit && demo.read(state.outcome)) return true;
        const position = demo.xy()[axis];
        return increasing ? position >= goal - 20 : position <= goal + 20;
    };
    holdUntil(demo, up, reached, 1800, settle);
}

function walkRoute(demo, target, gate = false) {
    const path = routeTo(demo, target, gate);
    if (gate) path.pop();
    const headings = new Map([[-width, 0], [1, 16], [width, 32], [-1, 48]]);
    for (let i = 1; i < path.length; i++) {
        const stride = path[i] - path[i - 1];
        while (i + 1 < path.length && path[i + 1] - path[i] === stride) i++;
        const heading = headings.get(stride);
        face(demo, heading, 0);
        const exit = i === path.length - 1 && target.kind === 4;
        walkRun(demo, [path[i] % width, Math.floor(path[i] / width)], heading, exit, 0);
    }
    if (gate) {
        const last = path.at(-1);
        const heading = headings.get(target.y * width + target.x - last);
        face(demo, heading, 0);
        const axis = heading % 32 ? 0 : 1;
        const center = (axis === 0 ? target.x : target.y) * 256 + 128;
        holdUntil(demo, up, () => Math.abs(demo.xy()[axis] - center) < 224, 500, 0);
        press(demo, "shift", true);
        assert.equal(demo.read(target.address), 0);
        assert.equal(demo.read(mapAddress(target.x, target.y)), 0);
        walkRun(demo, [target.x, target.y], heading, false, 0);
    }
}

function playCampaign(frequency) {
    const difficulty = frequency === 50 ? 2 : 1;
    const demo = startCampaign(frequency, difficulty);
    checkMenu(demo, frequency);
    for (let sector = 0; sector < names.length; sector++) {
        checkSector(demo, sector, difficulty);
        checkPlacement(demo);
        checkTrack(demo, sector, frequency);
        const props = entities(demo, state.props, state.propEnd);
        const keys = props.filter(({ kind }) => kind === 2).sort((a, b) => a.arg - b.arg);
        const gates = props.filter(({ kind }) => kind === 3).sort((a, b) => a.arg - b.arg);
        assert.equal(keys.length, 4);
        assert.deepEqual(keys.map(({ arg }) => arg), [1, 2, 4, 8]);
        assert.deepEqual(gates.map(({ arg }) => arg), [1, 2, 4, 8]);

        // Disable enemies only in this run to time traversal on a known route.
        for (const { address } of entities(demo, state.enemies, state.enemyEnd)) demo.write(address, 0);
        const before = demo.elapsed();
        for (const [i, key] of keys.entries()) {
            walkRoute(demo, key);
            assert.equal(demo.read(key.address), 0);
            assert.equal(demo.read(state.keysHeld), (1 << (i + 1)) - 1);
            walkRoute(demo, gates[i], true);
            if (i === 1) {
                press(demo, "menu", true);
                checkPlayerMarker(demo);
                press(demo, "menu", true);
            }
        }
        walkRoute(demo, props.find(({ kind }) => kind === 4));
        assert.equal(demo.read(state.outcome), sector === names.length - 1 ? 3 : 2);
        const seconds = (demo.elapsed() - before) / frequency;
        assert.ok(seconds >= 120, `${names[sector]} levou só ${seconds.toFixed(1)} s.`);
        console.log(`${names[sector]}, ${frequency} Hz: ${seconds.toFixed(1)} s de rota guiada sem combate.`);
        demo.run(12);
        checkVideo(demo);
        if (sector === names.length - 1 && frequency === 60 && endingPath) saveFrame(demo.frame, endingPath);
        press(demo, "keys", space);
    }
    assert.equal(demo.read(state.outcome), 4);
    checkTitleArt(demo);
    press(demo, "keys", space);
    checkSector(demo, 0, difficulty);
}

const expanded = boot(60, 2);
expanded.run(200);
assert.equal(expanded.read(state.outcome), 4, "O cartucho deve iniciar também em um subslot.");
for (let i = 0; i < 8 && (expanded.read(0xf12c) & 7) !== 4; i++) expanded.run(1);
const phases = new Set();
for (let i = 0; i < 4; i++) {
    phases.add(expanded.read(state.titlePhase));
    checkTitleArt(expanded);
    expanded.run(8);
}
assert.equal(phases.size, 4, "A animação da abertura deve apresentar seus quatro quadros de arte.");
press(expanded, "keys", space);
checkSector(expanded, 0);

for (const frequency of [60, 50]) {
    checkOpening(frequency);
    checkDifficulty(frequency);
    checkWallEdges(frequency, 1, 0);
    checkWallEdges(frequency, 2, 16);
    checkSlopedWall(frequency, frequency === 60 ? 1 : 2);
    checkMinimap(frequency);
    checkMusicControls(frequency);
    checkArena(frequency);
    playCampaign(frequency);
    console.log(`MSX1 64 KiB, ${frequency} Hz: campanha, portas, chaves, combate, cura, mapa e três faixas OK.`);
}
