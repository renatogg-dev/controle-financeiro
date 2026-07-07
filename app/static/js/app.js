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
