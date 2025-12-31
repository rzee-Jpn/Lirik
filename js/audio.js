// ===============================
// AUDIO QURAN - AUTO GENERATE
// ===============================

function pad3(n) {
  return String(n).padStart(3, "0");
}

function getAyatAudioUrl(surah, ayat) {
  return `https://everyayah.com/data/aziz_alili_128kbps/${pad3(surah)}${pad3(ayat)}.mp3`;
}

const audioPlayer = new Audio();
let activeBtn = null;

document.addEventListener("click", (e) => {
  const btn = e.target.closest("[data-audio]");
  if (!btn) return;

  const src = btn.dataset.audio;

  // toggle pause
  if (audioPlayer.src === src && !audioPlayer.paused) {
    audioPlayer.pause();
    btn.textContent = "🔊 Play";
    return;
  }

  if (activeBtn) activeBtn.textContent = "🔊 Play";

  audioPlayer.src = src;
  audioPlayer.play();

  btn.textContent = "⏸ Pause";
  activeBtn = btn;
});

audioPlayer.addEventListener("ended", () => {
  if (activeBtn) activeBtn.textContent = "🔊 Play";
});

audioPlayer.addEventListener("error", () => {
  alert("Audio ayat tidak tersedia");
  if (activeBtn) activeBtn.textContent = "🔊 Play";
});