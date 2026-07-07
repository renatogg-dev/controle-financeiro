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

// Dashboard charts: reads JSON embedded by the server into <script> tags and
// (re)renders Chart.js instances. Re-run on every HTMX swap that brings in
// fresh chart data (e.g. changing the dashboard's month filter), since a
// plain DOM swap doesn't re-execute any chart initialization on its own.
let dashboardCharts = {};

function destroyDashboardCharts() {
    Object.values(dashboardCharts).forEach((chart) => chart.destroy());
    dashboardCharts = {};
}

function initDashboardCharts() {
    if (typeof Chart === "undefined") return;
    destroyDashboardCharts();

    const categoryDataEl = document.getElementById("category-breakdown-data");
    const categoryCanvas = document.getElementById("category-chart");
    if (categoryDataEl && categoryCanvas) {
        const data = JSON.parse(categoryDataEl.textContent);
        dashboardCharts.category = new Chart(categoryCanvas, {
            type: "doughnut",
            data: {
                labels: data.map((d) => d.category),
                datasets: [
                    {
                        data: data.map((d) => d.amount),
                        backgroundColor: data.map((d) => d.color),
                        borderWidth: 0,
                    },
                ],
            },
            options: { cutout: "65%", plugins: { legend: { position: "bottom" } } },
        });
    }

    const seriesDataEl = document.getElementById("monthly-series-data");
    const seriesCanvas = document.getElementById("series-chart");
    if (seriesDataEl && seriesCanvas) {
        const data = JSON.parse(seriesDataEl.textContent);
        dashboardCharts.series = new Chart(seriesCanvas, {
            type: "bar",
            data: {
                labels: data.map((d) => d.month),
                datasets: [
                    { label: "Receitas", data: data.map((d) => d.income), backgroundColor: "#0d9488", borderRadius: 4 },
                    { label: "Despesas", data: data.map((d) => d.expense), backgroundColor: "#c2410c", borderRadius: 4 },
                ],
            },
            options: { plugins: { legend: { position: "bottom" } }, scales: { y: { beginAtZero: true } } },
        });
    }
}

document.addEventListener("DOMContentLoaded", initDashboardCharts);
document.body.addEventListener("htmx:afterSwap", (event) => {
    if (event.detail.target.querySelector?.("#category-breakdown-data, #monthly-series-data")) {
        initDashboardCharts();
    }
});
