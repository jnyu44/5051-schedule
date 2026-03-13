/**
 * 5051 Schedule App — Frontend JavaScript
 *
 * Fetches the schedule from /api/schedule, renders an editable HTML table,
 * and auto-saves cell changes via PUT /api/cell.
 */

// ── State ──────────────────────────────────────────────────────────
let scheduleData = { columns: [], weeks: [] };

// ── Helpers ────────────────────────────────────────────────────────
async function api(url, opts = {}) {
    const res = await fetch(url, {
        headers: { "Content-Type": "application/json" },
        ...opts,
    });
    return res.json();
}

// ── Load & Render ─────────────────────────────────────────────────
async function loadSchedule() {
    scheduleData = await api("/api/schedule");
    render();
}

function render() {
    const container = document.getElementById("schedule-container");
    if (!container) return;

    const { columns, weeks } = scheduleData;

    if (weeks.length === 0) {
        container.innerHTML = `
            <div style="text-align:center; padding:3rem; color:#9096a2;">
                <p style="font-size:1.1rem; margin-bottom:0.5rem;">No weeks added yet.</p>
                ${IS_EDITOR ? '<p>Click <b>+ Add Week</b> above to get started.</p>' : '<p>The schedule will appear here once the team adds content.</p>'}
            </div>`;
        return;
    }

    let html = "";

    for (const week of weeks) {
        html += `<div class="week-section">`;
        html += `<div class="week-header">
                    <span>${escHtml(week.label)}${week.start_date ? ' — ' + formatDate(week.start_date) : ''}</span>
                    ${IS_EDITOR ? `<div class="week-header-actions">
                        <button class="btn" onclick="addRow(${week.id}, ${getMaxSort(week)})">+ Row</button>
                    </div>` : ''}
                 </div>`;

        html += `<table class="schedule-table">`;
        html += `<thead><tr>`;
        for (const col of columns) {
            html += `<th>${escHtml(col.name)}</th>`;
        }
        if (IS_EDITOR) html += `<th class="row-actions"></th>`;
        html += `</tr></thead>`;

        html += `<tbody>`;
        if (week.rows.length === 0) {
            html += `<tr><td colspan="${columns.length + (IS_EDITOR ? 1 : 0)}"
                         style="text-align:center; color:#9096a2; padding:1rem;">
                         No rows yet${IS_EDITOR ? ' — click + Row' : ''}
                     </td></tr>`;
        } else {
            for (const row of week.rows) {
                html += `<tr data-row-id="${row.id}">`;
                for (const col of columns) {
                    const val = row.cells[String(col.id)] || "";
                    const isConfirmed = col.name.toLowerCase() === "confirmed" && val.toUpperCase() === "Y";
                    const cellClass = isConfirmed ? "cell-confirmed" : "";

                    if (IS_EDITOR) {
                        html += `<td class="${cellClass}" contenteditable="true"
                                     data-row-id="${row.id}" data-col-id="${col.id}"
                                     data-original="${escAttr(val)}"
                                     onblur="onCellBlur(this)">${escHtml(val)}</td>`;
                    } else {
                        html += `<td class="${cellClass}">${escHtml(val)}</td>`;
                    }
                }
                if (IS_EDITOR) {
                    html += `<td class="row-actions">
                                <button class="delete-row-btn" onclick="deleteRow(${row.id})" title="Delete row">🗑</button>
                             </td>`;
                }
                html += `</tr>`;
            }
        }
        html += `</tbody></table></div>`;
    }

    container.innerHTML = html;
}

// ── Cell edit (auto-save on blur) ──────────────────────────────────
async function onCellBlur(td) {
    const newVal = td.textContent.trim();
    const original = td.getAttribute("data-original");
    if (newVal === original) return;  // No change

    const rowId = td.getAttribute("data-row-id");
    const colId = td.getAttribute("data-col-id");

    td.style.opacity = "0.5";
    await api("/api/cell", {
        method: "PUT",
        body: JSON.stringify({ row_id: parseInt(rowId), column_id: parseInt(colId), value: newVal }),
    });
    td.setAttribute("data-original", newVal);
    td.style.opacity = "1";

    // Re-apply confirmed styling
    if (newVal.toUpperCase() === "Y") {
        td.classList.add("cell-confirmed");
    } else {
        td.classList.remove("cell-confirmed");
    }
}

// ── Row operations ────────────────────────────────────────────────
async function addRow(weekId, afterSort) {
    await api("/api/row", {
        method: "POST",
        body: JSON.stringify({ week_id: weekId, after_sort: afterSort }),
    });
    await loadSchedule();
}

async function deleteRow(rowId) {
    if (!confirm("Delete this row?")) return;
    await api(`/api/row/${rowId}`, { method: "DELETE" });
    await loadSchedule();
}

// ── Week operations ───────────────────────────────────────────────
function showAddWeekModal() {
    document.getElementById("add-week-modal").classList.remove("hidden");
    document.getElementById("week-label").focus();
}

async function addWeek() {
    const label = document.getElementById("week-label").value.trim();
    const startDate = document.getElementById("week-start").value;
    if (!label) return;

    await api("/api/week", {
        method: "POST",
        body: JSON.stringify({ label, start_date: startDate || null }),
    });

    closeModal("add-week-modal");
    document.getElementById("week-label").value = "";
    document.getElementById("week-start").value = "";
    await loadSchedule();
}

// ── Column operations ─────────────────────────────────────────────
function showAddColumnModal() {
    document.getElementById("add-column-modal").classList.remove("hidden");
    document.getElementById("column-name").focus();
}

async function addColumn() {
    const name = document.getElementById("column-name").value.trim();
    if (!name) return;

    await api("/api/column", {
        method: "POST",
        body: JSON.stringify({ name }),
    });

    closeModal("add-column-modal");
    document.getElementById("column-name").value = "";
    await loadSchedule();
}

// ── Change log ────────────────────────────────────────────────────
async function toggleChangelog() {
    const panel = document.getElementById("changelog-panel");
    panel.classList.toggle("hidden");
    if (!panel.classList.contains("hidden")) {
        const data = await api("/api/changelog");
        const container = document.getElementById("changelog-entries");
        if (data.entries.length === 0) {
            container.innerHTML = '<p style="color:#9096a2; font-size:0.85rem;">No changes yet.</p>';
            return;
        }
        container.innerHTML = data.entries.map(e => `
            <div class="log-entry">
                <div class="log-meta">
                    <span class="log-user">${escHtml(e.user)}</span>
                    <span>${formatTimestamp(e.timestamp)}</span>
                </div>
                <div class="log-details">${escHtml(e.details)}</div>
            </div>`).join("");
    }
}

// ── Modals ─────────────────────────────────────────────────────────
function closeModal(id) {
    document.getElementById(id).classList.add("hidden");
}

// Close modals on backdrop click
document.addEventListener("click", (e) => {
    if (e.target.classList.contains("modal")) {
        e.target.classList.add("hidden");
    }
});

// ── Utilities ─────────────────────────────────────────────────────
function escHtml(str) {
    const div = document.createElement("div");
    div.textContent = str || "";
    return div.innerHTML;
}

function escAttr(str) {
    return (str || "").replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function getMaxSort(week) {
    if (!week.rows.length) return 0;
    return Math.max(...week.rows.map(r => r.sort_order));
}

function formatDate(isoDate) {
    if (!isoDate) return "";
    const d = new Date(isoDate + "T00:00:00");
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

function formatTimestamp(iso) {
    const d = new Date(iso);
    return d.toLocaleString("en-US", {
        month: "short", day: "numeric",
        hour: "numeric", minute: "2-digit",
    });
}

// ── Init ──────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", loadSchedule);
