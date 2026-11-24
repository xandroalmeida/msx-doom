const languageButtons = [...document.querySelectorAll("[data-language]")];
const localized = [
  ...[...document.querySelectorAll("[data-copy]")].map((element) => ({
    key: element.dataset.copy, initial: element.textContent,
    write: (value) => { element.textContent = value; },
  })),
  ...[...document.querySelectorAll("[data-alt], [data-label]")].map((element) => {
    const attribute = element.dataset.alt ? "alt" : "aria-label";
    return {
      key: element.dataset.alt || element.dataset.label, initial: element.getAttribute(attribute),
      write: (value) => { element.setAttribute(attribute, value); },
    };
  }),
];
const consoleScreen = document.querySelector("#console-screen");
const poster = document.querySelector("#console-poster");
const launchText = poster.querySelector("[data-copy=launch]");
const releaseVersion = document.querySelector("#release-version");
const description = document.querySelector('meta[name="description"]');
const externalPlayer = document.querySelector("#external-player");
let language;
let frame;
let starting = false;

function selectLanguage(code, persist = false) {
  language = code;
  const locale = siteLocales[code];
  document.documentElement.lang = locale.lang;
  document.title = locale.title;
  description.content = locale.description;
  for (const item of localized) item.write(locale[item.key] ?? item.initial);
  for (const button of languageButtons) {
    button.setAttribute("aria-pressed", String(button.dataset.language === code));
  }
  if (frame) frame.title = locale.frameTitle;
  if (starting) launchText.textContent = locale.loading;

  if (persist) {
    const url = new URL(location.href);
    url.searchParams.set("lang", code);
    history.replaceState(null, "", url);
    try { localStorage.setItem("posto-umbra-language", code); } catch {}
  }
}

function initialLanguage() {
  let saved;
  try { saved = localStorage.getItem("posto-umbra-language"); } catch {}
  const requested = new URLSearchParams(location.search).get("lang");
  return [requested, saved, navigator.language?.slice(0, 2)].find((code) => Object.hasOwn(siteLocales, code)) ?? "pt";
}

function updateRomLinks({version, romId}) {
  const rom = new URL(romId ? `rom/${romId}/posto-umbra.rom` : "posto-umbra.rom", location.href);
  if (version) {
    releaseVersion.textContent = `MSX1 · ${version}`;
    for (const link of document.querySelectorAll("a[download]")) link.href = rom.href;
  }
  const url = new URL("https://webmsx.org/cbios/");
  url.searchParams.set("MACHINE", "MSX1A");
  url.searchParams.set("RAMNORMAL_SIZE", "64");
  url.searchParams.set("ROM", rom.href);
  externalPlayer.href = url.href;
}

async function loadRelease() {
  try {
    const response = await fetch("release.json", {cache: "no-store", signal: AbortSignal.timeout(4000)});
    if (!response.ok) return {};
    const {version, romId} = await response.json();
    return typeof version === "string" && /^[a-f0-9]{16}$/.test(romId) ? {version, romId} : {};
  } catch {
    return {};
  }
}

selectLanguage(initialLanguage());
for (const button of languageButtons) {
  button.addEventListener("click", () => selectLanguage(button.dataset.language, true));
}
updateRomLinks({});
const release = loadRelease().then((metadata) => {
  updateRomLinks(metadata);
  return metadata;
});

async function startEmulator() {
  if (frame || starting) return;
  starting = true;
  launchText.textContent = siteLocales[language].loading;
  poster.querySelector("button").disabled = true;
  const current = await loadRelease();
  const metadata = current.romId ? current : await release;
  updateRomLinks(metadata);

  const url = new URL("player.html", location.href);
  url.searchParams.set("lang", language);
  if (metadata.romId) url.searchParams.set("rom", metadata.romId);
  frame = document.createElement("iframe");
  frame.src = url.href;
  frame.title = siteLocales[language].frameTitle;
  frame.allow = "autoplay; fullscreen; gamepad";
  frame.allowFullscreen = true;
  poster.hidden = true;
  consoleScreen.append(frame);
  frame.focus();
  starting = false;
}

for (const trigger of document.querySelectorAll("[data-start]")) {
  trigger.addEventListener("click", startEmulator);
}
