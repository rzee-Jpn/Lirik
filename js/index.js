document.addEventListener("DOMContentLoaded", () => {
  /* ===== AUDIO URL GENERATOR ===== */
  function pad3(n) {
    return String(n).padStart(3, "0");
  }

  function getAyatAudioUrl(surah, ayat) {
    return `https://everyayah.com/data/aziz_alili_128kbps/${pad3(surah)}${pad3(ayat)}.mp3`;
  }
  const params = new URLSearchParams(location.search);
  const surah = Number(params.get("surah"));
  const ayatDiv = document.getElementById("ayat");
  const judul = document.getElementById("judul");
  const headbar = document.getElementById("headbar");
  const footerBrand = document.getElementById("footerBrand");
  const toggle = document.getElementById("toggleArti");
  const sidebar = document.getElementById("sidebar");
  const toggleSidebar = document.getElementById("toggleSidebar");
  const closeSidebar = document.getElementById("closeSidebar");
  const overlay = document.getElementById("overlay");
  const themeButtons = document.querySelectorAll(".theme-options button");
  const lastReadEl = document.getElementById("lastRead");
  const bookmarkListEl = document.getElementById("bookmarkList");
  const clearBookmarksBtn = document.getElementById("clearBookmarks");

  if (!ayatDiv || !judul || !headbar) return;

  /* ================= THEME ================= */
  const THEMES = ["theme-light","theme-dark","theme-sepia","theme-paper"];
  const savedTheme = localStorage.getItem("theme") || "theme-paper";
  document.body.classList.remove(...THEMES);
  document.body.classList.add(savedTheme);

  themeButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const t = btn.dataset.theme;
      if (!t) return;
      document.body.classList.remove(...THEMES);
      document.body.classList.add(t);
      localStorage.setItem("theme", t);
    });
  });

  /* ================= SIDEBAR ================= */
  function openSidebar() {
    overlay.classList.remove("hidden");
    overlay.classList.add("visible");
    sidebar.classList.add("open");
    sidebar.setAttribute("aria-hidden","false");
    sidebar.style.pointerEvents = "auto";
    gsap?.to(sidebar, { right: 0, duration: .28, ease: "power2.out" });
  }

  function closeSidebarFn() {
    gsap?.to(sidebar, {
      right: "-100vw",
      duration: .26,
      ease: "power2.in",
      onComplete: () => {
        sidebar.classList.remove("open");
        sidebar.setAttribute("aria-hidden","true");
        sidebar.style.pointerEvents = "none";
      }
    });
    gsap?.to(overlay, {
      opacity: 0,
      duration: .22,
      onComplete: () => {
        overlay.classList.add("hidden");
        overlay.classList.remove("visible");
      }
    });
  }

  toggleSidebar?.addEventListener("click", openSidebar);
  closeSidebar?.addEventListener("click", closeSidebarFn);
  overlay?.addEventListener("click", closeSidebarFn);

  /* ================= BOOKMARK ================= */
  function getBookmarks() {
    try { return JSON.parse(localStorage.getItem("bookmarks") || "[]"); }
    catch { return []; }
  }
  function saveBookmarks(arr) {
    localStorage.setItem("bookmarks", JSON.stringify(arr));
  }
  function updateBookmarkList() {
    const arr = getBookmarks();
    bookmarkListEl.innerHTML = "";
    if (!arr.length) {
      bookmarkListEl.innerText = "Belum ada";
      return;
    }
    arr.forEach((b, idx) => {
      const row = document.createElement("div");
      row.className = "bookmark-item";
      row.innerHTML = `
        <a href="index.html?surah=${b.surah}">Surah ${b.surah} — ayat ${b.ayat}</a>
        <button class="btn-ghost">Hapus</button>
      `;
      row.querySelector("button").onclick = e => {
        e.stopPropagation();
        arr.splice(idx,1);
        saveBookmarks(arr);
        updateBookmarkList();
      };
      bookmarkListEl.appendChild(row);
    });
  }

  clearBookmarksBtn?.addEventListener("click", () => {
    localStorage.removeItem("bookmarks");
    updateBookmarkList();
  });

  /* ================= LOAD SURAH ================= */
  let ayatData = [];
  let renderedCount = 0;
  const BATCH_SIZE = 20;

  async function loadSurah(n) {
    if (!n) {
      ayatDiv.innerHTML = "<p style='text-align:center'>Silakan pilih surah</p>";
      return;
    }

    const res = await fetch(`./surah/${n}.json`);
    const data = await res.json();
    const s = data.text ? data : Object.values(data)[0];

    judul.textContent = `${s.name_latin} (${s.name})`;
    ayatDiv.innerHTML = "";
    ayatData = [];

    Object.keys(s.text).forEach(no => {
      ayatData.push({
        no,
        text: s.text[no],
        terjemah: s.translations?.id?.text?.[no] || ""
      });
    });

    renderedCount = 0;
    renderNextBatch();
    updateBookmarkList();
  }

  function renderNextBatch() {
    ayatData.slice(renderedCount, renderedCount + BATCH_SIZE).forEach(a => {
      const el = document.createElement("article");
      el.className = "ayat";
      el.dataset.no = a.no;
      el.dataset.text = a.text;
      const audioUrl = getAyatAudioUrl(surah, a.no);

el.innerHTML = `
  <div class="arab">
    <span class="no">${a.no}</span>
    ${a.text}
    <button
      class="audio-btn"
      data-audio="${audioUrl}"
      aria-label="Putar audio ayat ${a.no}">
      🔊
    </button>
  </div>
  <div class="arti">${a.terjemah}</div>
`;


      ayatDiv.appendChild(el);
    });
    renderedCount += BATCH_SIZE;
  }

  window.addEventListener("scroll", () => {
    if (window.innerHeight + scrollY > document.body.offsetHeight - 250) {
      renderNextBatch();
    }
  });

  loadSurah(surah);

  /* ================= TOGGLE TERJEMAH (FIX UTAMA) ================= */
  toggle?.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation(); // 🔥 FIX PENTING

    document.body.classList.toggle("hide-translation");

    const hidden = document.body.classList.contains("hide-translation");
    toggle.setAttribute("aria-pressed", String(!hidden));
    toggle.textContent = hidden ? "Tampilkan Terjemah" : "Sembunyikan Terjemah";
  });

  /* ================= GLOBAL CLICK ================= */
  document.addEventListener("click", (e) => {
    if (
      e.target.closest("#sidebar") ||
      e.target.closest("#toggleSidebar") ||
      e.target.closest(".theme-options") ||
      e.target.closest("#toggleArti")
    ) return;

    if (e.target.closest(".ayat")) {
      e.target.closest(".ayat").classList.toggle("focus");
    }
  });

/* ===== AUDIO PLAYER GLOBAL ===== */
  const audioPlayer = new Audio();
  let activeAudioBtn = null;

  document.addEventListener("click", (e) => {
    const btn = e.target.closest(".audio-btn");
    if (!btn) return;

    e.stopPropagation();

    const src = btn.dataset.audio;

    if (audioPlayer.src === src && !audioPlayer.paused) {
      audioPlayer.pause();
      btn.textContent = "🔊";
      return;
    }

    if (activeAudioBtn) activeAudioBtn.textContent = "🔊";

    audioPlayer.src = src;
    audioPlayer.play().catch(() => {
      alert("Audio ayat tidak tersedia");
    });

    btn.textContent = "⏸";
    activeAudioBtn = btn;
  });

  audioPlayer.addEventListener("ended", () => {
    if (activeAudioBtn) activeAudioBtn.textContent = "🔊";
  });
});