const parameters = new URLSearchParams(location.search);
const messages = {
  pt: ["pt-BR", "Não foi possível carregar o WebMSX. Tente abrir o jogo em outra aba ou baixe a ROM."],
  en: ["en", "WebMSX could not load. Try opening the game in a new tab or downloading the ROM."],
  es: ["es", "No se pudo cargar WebMSX. Abre el juego en otra pestaña o descarga la ROM."],
};
const requested = parameters.get("lang");
const [lang, errorMessage] = Object.hasOwn(messages, requested) ? messages[requested] : messages.pt;
document.documentElement.lang = lang;

if (window.WMSX) {
  const id = parameters.get("rom");
  const rom = new URL(/^[a-f0-9]{16}$/.test(id) ? `rom/${id}/posto-umbra.rom` : "posto-umbra.rom", location.href);
  Object.assign(window.WMSX, {
    ALLOW_URL_PARAMETERS: false,
    MACHINE: "MSX1A",
    RAMNORMAL_SIZE: 64,
    CARTRIDGE1_URL: rom.href,
    AUTO_POWER_ON_DELAY: 0,
    MEDIA_CHANGE_DISABLED: true,
    SCREEN_FULLSCREEN_MODE: 2,
    SCREEN_DEFAULT_ASPECT: 1,
    SCREEN_FILTER_MODE: 0,
  });
} else {
  const error = document.querySelector("#player-error");
  error.textContent = errorMessage;
  error.hidden = false;
}
