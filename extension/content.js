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
      const m = url.match(/-p(\d+)(?:[-/.]|$)/);
      if (m) return m[1];
    }
    // Fallback: use full URL as ID
    return url;
  }

  function extractPrice(product) {
    const offers = Array.isArray(product.offers) ? product.offers[0] : product.offers;
    if (offers && offers.price != null) {
      return parseFloat(String(offers.price).replace(",", "."));
    }
    // CSS fallbacks
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
        const cleaned = raw.replace(/[^\d.,]/g, "").replace(",", ".");
        const val = parseFloat(cleaned);
        if (!isNaN(val) && val > 0) return val;
      }
    }
    return null;
  }

  function extractImage(product) {
    const img = product.image;
    if (Array.isArray(img)) return img[0] || null;
    if (typeof img === "string") return img;
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

    const product = extractJsonLdProduct();
    if (!product) {
      showNotification("Could not find product data on this page.", true);
      return;
    }

    const title = product.name || document.querySelector("h1")?.textContent?.trim() || "Unknown Product";
    const price = extractPrice(product);
    const imageUrl = extractImage(product);
    const externalId = extractExternalId(retailerId);

    if (!price) {
      showNotification("Could not extract price from this page.", true);
      return;
    }

    btn.classList.add("pricewatch-btn--loading");
    btn.textContent = "Adding...";

    try {
      const response = await fetch(PRICEWATCH_API, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
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
        btn.textContent = "Added!";
        btn.classList.remove("pricewatch-btn--loading");
        btn.classList.add("pricewatch-btn--success");
        showNotification(`"${title.slice(0, 50)}" added to PriceWatch!`);
        setTimeout(() => {
          btn.textContent = "+ Add to PriceWatch";
          btn.classList.remove("pricewatch-btn--success");
        }, 3000);
      } else {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || "Server error");
      }
    } catch (e) {
      btn.textContent = "Failed — backend running?";
      btn.classList.remove("pricewatch-btn--loading");
      btn.classList.add("pricewatch-btn--error");
      showNotification("Error: " + e.message, true);
      setTimeout(() => {
        btn.textContent = "+ Add to PriceWatch";
        btn.classList.remove("pricewatch-btn--error");
      }, 4000);
    }
  }

  function injectButton() {
    if (document.getElementById(BUTTON_ID)) return;

    const product = extractJsonLdProduct();
    if (!product) return;

    const btn = document.createElement("button");
    btn.id = BUTTON_ID;
    btn.className = "pricewatch-btn";
    btn.textContent = "+ Add to PriceWatch";
    btn.addEventListener("click", handleClick);
    document.body.appendChild(btn);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", injectButton);
  } else {
    injectButton();
  }
})();
