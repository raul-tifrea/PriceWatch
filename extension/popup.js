const SUPPORTED = ["cel.ro", "pcgarage.ro", "altex.ro"];

chrome.tabs.query({ active: true, currentWindow: true }, ([tab]) => {
  if (!tab) return;
  const host = new URL(tab.url).hostname.replace("www.", "");
  const isSupported = SUPPORTED.some((s) => host.includes(s));

  const rows = document.querySelectorAll(".site-row");
  rows.forEach((row) => {
    const siteName = row.textContent.trim();
    if (isSupported && host.includes(siteName)) {
      row.style.color = "#4ade80";
      row.querySelector(".dot").style.background = "#22c55e";
    }
  });
});
