const select = document.getElementById("themeSelect");

if (select) {
  const saved = localStorage.theme || "theme-paper";
  document.body.className = saved;
  select.value = saved;

  select.onchange = () => {
    document.body.className = select.value;
    localStorage.theme = select.value;
  };
}