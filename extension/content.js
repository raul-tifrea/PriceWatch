(function () {
  const PRICEWATCH_API = "http://localhost:8000/api/products/from-extension";
  const BUTTON_ID = "pricewatch-btn";
  const SITE_CONFIG = {
    "cel.ro": { retailer_id: "cel.ro" },
    "pcgarage.ro": { retailer_id: "pcgarage.ro" },
    "altex.ro": { retailer_id: "altex.ro" },
  };
  function getRetailerId() {
    const host = location.hostname.replace("www.", "");
    for (const key of Object.keys(SITE_CONFIG)) {
      if (host.includes(key)) return SITE_CONFIG[key].retailer_id;
    }
    return null;
  }
  function extractJsonLdProduct() {
    const scripts = document.querySelectorAll('script[type="application/ld+json"]');
    for (const script of scripts) {
      try {
        const data = JSON.parse(script.textContent);
        const items = Array.isArray(data) ? data : [data];
        for (const item of items) {
          if (item["@type"] === "Product") return item;
        }
      } catch (_) {}
    }
    return null;
  }
  function extractExternalId(retailerId) {
    const url = location.href;
    if (retailerId === "altex.ro") {
      const m = url.match(/\/cpd\/([^/]+)\/?$/);
      if (m) return m[1];
    }
    if (retailerId === "pcgarage.ro") {
      const m = url.match(/-p(\d+)(?:[./]|$)/);
      if (m) return m[1];
    }
    if (retailerId === "cel.ro") {
      const form = document.querySelector("form[name='buy'] input[name='products_id']");
      if (form) return form.value;
      const m = url.match(/-p([a-zA-Z0-9_-]+)(?:[-/.]|$)/);
      if (m) return m[1];
    }
    return url;
  }
  function parseRomanianPrice(rawStr) {
    let s = String(rawStr).replace(/[^\d.,]/g, "");
    if (!s) return null;
    const lastComma = s.lastIndexOf(',');
    const lastDot = s.lastIndexOf('.');
    if (lastComma > -1 && lastDot > -1) {
      if (lastComma > lastDot) {
        s = s.replace(/\./g, "").replace(",", ".");
      } else {
        s = s.replace(/,/g, "");
      }
    } else if (lastComma > -1) {
      const parts = s.split(',');
      if (parts[parts.length - 1].length === 3) {
        s = s.replace(/,/g, "");
      } else {
        s = s.replace(",", ".");
      }
    } else if (lastDot > -1) {
      const parts = s.split('.');
      if (parts[parts.length - 1].length === 3) {
        s = s.replace(/\./g, "");
      }
    }
    const val = parseFloat(s);
    return isNaN(val) ? null : val;
  }
  function extractPrice(product) {
    if (product) {
      const offers = Array.isArray(product.offers) ? product.offers[0] : product.offers;
      if (offers && offers.price != null) {
        const p = parseRomanianPrice(offers.price);
        if (p != null && p > 0) return p;
      }
    }
    const selectors = [
      "[itemprop='price']",
      ".Price-int",
      "span.price",
      ".product-price",
      "[data-testid='price']",
    ];
    for (const sel of selectors) {
      const el = document.querySelector(sel);
      if (el) {
        const raw = el.getAttribute("content") || el.textContent || "";
        const p = parseRomanianPrice(raw);
        if (p != null && p > 0) return p;
      }
    }
    return null;
  }
  function extractImage(product) {
    if (product) {
      const img = product.image;
      if (Array.isArray(img)) return img[0] || null;
      if (typeof img === "string") return img;
    }
    const el = document.querySelector(".product-image img, .gallery-image img, [itemprop='image']");
    return el ? (el.src || el.getAttribute("content")) : null;
  }
  function showNotification(message, isError = false) {
    const existing = document.getElementById("pricewatch-notif");
    if (existing) existing.remove();
    const notif = document.createElement("div");
    notif.id = "pricewatch-notif";
    notif.className = isError ? "pricewatch-notif pricewatch-notif--error" : "pricewatch-notif pricewatch-notif--success";
    notif.textContent = message;
    document.body.appendChild(notif);
    setTimeout(() => notif.remove(), 4000);
  }
  async function handleClick() {
    const btn = document.getElementById(BUTTON_ID);
    if (!btn) return;
    const retailerId = getRetailerId();
    if (!retailerId) return;
    const { pw_token } = await chrome.storage.local.get(["pw_token"]);
    if (!pw_token) {
      window.open("http://localhost:5173", "_blank");
      return;
    }
    const product = extractJsonLdProduct();
    const title = (product && product.name) || document.querySelector("h1")?.textContent?.trim() || "Unknown Product";
    const price = extractPrice(product);
    const imageUrl = extractImage(product);
    const externalId = extractExternalId(retailerId);
    if (!price) {
      showNotification("Could not extract price from this page.", true);
      return;
    }
    btn.classList.add("pricewatch-btn--loading");
    btn.querySelector(".pw-text").textContent = "Adding...";
    try {
      const response = await fetch(PRICEWATCH_API, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${pw_token}`,
        },
        body: JSON.stringify({
          name: title,
          url: location.href,
          retailer_id: retailerId,
          title: title,
          price: price,
          external_id: String(externalId),
          image_url: imageUrl,
          currency: "RON",
        }),
      });
      if (response.ok) {
        btn.querySelector(".pw-text").textContent = "Added!";
        btn.classList.remove("pricewatch-btn--loading");
        btn.classList.add("pricewatch-btn--success");
        showNotification(`"${title.slice(0, 50)}" added to PriceWatch!`);
        setTimeout(() => {
          btn.querySelector(".pw-text").textContent = "Add to PriceWatch";
          btn.classList.remove("pricewatch-btn--success");
        }, 3000);
      } else if (response.status === 401) {
        btn.classList.remove("pricewatch-btn--loading");
        await chrome.storage.local.remove(["pw_token", "pw_email"]);
        window.open("http://localhost:5173", "_blank");
      } else if (response.status === 409) {
        btn.querySelector(".pw-text").textContent = "Already tracked";
        btn.classList.remove("pricewatch-btn--loading");
        btn.classList.add("pricewatch-btn--success");
        showNotification("You are already tracking this product.");
        setTimeout(() => {
          btn.querySelector(".pw-text").textContent = "Add to PriceWatch";
          btn.classList.remove("pricewatch-btn--success");
        }, 3000);
      } else {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || "Server error");
      }
    } catch (e) {
      btn.querySelector(".pw-text").textContent = "Failed?";
      btn.classList.remove("pricewatch-btn--loading");
      btn.classList.add("pricewatch-btn--error");
      showNotification("Error: " + e.message, true);
      setTimeout(() => {
        btn.querySelector(".pw-text").textContent = "Add to PriceWatch";
        btn.classList.remove("pricewatch-btn--error");
      }, 4000);
    }
  }
  function isProductPage() {
    const retailerId = getRetailerId();
    if (!retailerId) return false;
    const url = location.href;
    const path = location.pathname;
    if (retailerId === "altex.ro") {
      return /\/cpd\/[^/]+/.test(path);
    }
    if (retailerId === "pcgarage.ro") {
      return /-p\d+(?:\.html|\/|$)/.test(path);
    }
    if (retailerId === "cel.ro") {
      return /-p[A-Za-z0-9_-]+-l\/?$/.test(path) || /-p[A-Za-z0-9_-]+\/?$/.test(path);
    }
    return !!extractJsonLdProduct();
  }
  function injectButton() {
    if (document.getElementById(BUTTON_ID)) return;
    if (!isProductPage()) return;
    const btn = document.createElement("button");
    btn.id = BUTTON_ID;
    btn.className = "pricewatch-btn";
    btn.innerHTML = `<span class="pw-icon"></span><span class="pw-text">Add to PriceWatch</span>`;
    btn.addEventListener("click", handleClick);
    document.body.appendChild(btn);
  }
  setInterval(() => {
    if (isProductPage()) {
      injectButton();
    } else {
      const existing = document.getElementById(BUTTON_ID);
      if (existing) existing.remove();
    }
  }, 1000);
})();