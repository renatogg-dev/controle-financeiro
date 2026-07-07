// Small glue script: no framework, no build step.
// 1) Attaches the CSRF token (from the <meta> tag rendered by base.html) to
//    every HTMX request header, since our HTMX routes are cookie-authenticated.
// 2) Reads embedded chart JSON and renders it with Chart.js (added when the
//    dashboard is wired up).

document.addEventListener("htmx:configRequest", (event) => {
    const token = document.querySelector('meta[name="csrf-token"]')?.content;
    if (token) {
        event.detail.headers["X-CSRF-Token"] = token;
    }
});

document.body.addEventListener("show-toast", (event) => {
    const { message, kind } = event.detail;
    const region = document.getElementById("toast-region");
    if (!region) return;

    const toast = document.createElement("div");
    const tone = kind === "error" ? "bg-expense" : "bg-income";
    toast.className = `rounded-md px-4 py-2.5 text-sm text-white shadow-lg ${tone}`;
    toast.textContent = message;
    region.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
});
