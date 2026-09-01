window.addEventListener("message", (event) => {
  if (event.source !== window) return;
  if (event.data && event.data.type === "PRICEWATCH_LOGOUT") {
    chrome.storage.local.remove(["pw_token", "pw_email"]);
  }
  if (event.data && event.data.type === "PRICEWATCH_LOGIN") {
    const { token, email } = event.data;
    if (token && email) {
      chrome.storage.local.set({ pw_token: token, pw_email: email });
    }
  }
});