// 通用工具函数

function formatDateTime(isoStr) {
    if (!isoStr) return "-";
    const d = new Date(isoStr);
    const pad = (n) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

function statusBadge(status, type) {
    const cls = type === "review" ? `review-${status}` : `status-${status}`;
    const labels = {
        pending: "执行中", success: "成功", failed: "失败",
        approved: "已通过", rejected: "已驳回"
    };
    return `<span class="badge ${cls}">${labels[status] || status}</span>`;
}

async function apiGet(url) {
    const res = await fetch(url);
    return res.json();
}

async function apiPost(url, data) {
    const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
    });
    return res.json();
}

async function apiUpload(url, formData) {
    const res = await fetch(url, { method: "POST", body: formData });
    return res.json();
}

function showToast(msg, type) {
    const container = document.getElementById("toast-container");
    if (!container) {
        const div = document.createElement("div");
        div.id = "toast-container";
        div.style.cssText = "position:fixed;top:20px;right:20px;z-index:9999;";
        document.body.appendChild(div);
    }
    const tc = document.getElementById("toast-container");
    const bg = type === "error" ? "bg-danger" : type === "warning" ? "bg-warning" : "bg-success";
    const toast = document.createElement("div");
    toast.className = `toast align-items-center text-white ${bg} border-0`;
    toast.setAttribute("role", "alert");
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${msg}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>`;
    tc.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
    bsToast.show();
    toast.addEventListener("hidden.bs.toast", () => toast.remove());
}

function renderTaskTable(containerId, tasks, columns, detailCallbackName, retryCallbackName) {
    const container = document.getElementById(containerId);
    if (!tasks || tasks.length === 0) {
        container.innerHTML = `<div class="empty-state"><i class="bi bi-inbox"></i><p>暂无数据</p></div>`;
        return;
    }
    let html = `<table class="table table-hover table-striped"><thead><tr>`;
    columns.forEach((col) => { html += `<th>${col.title}</th>`; });
    html += `<th>操作</th></tr></thead><tbody>`;
    tasks.forEach((t) => {
        html += `<tr>`;
        columns.forEach((col) => {
            html += `<td>${col.render ? col.render(t) : (t[col.field] || "-")}</td>`;
        });
        html += `<td>`;
        if (detailCallbackName) html += `<button class="btn btn-sm btn-outline-primary me-1" onclick="window['${detailCallbackName}'](${t.id})">详情</button>`;
        if (retryCallbackName && t.status === "failed") html += `<button class="btn btn-sm btn-outline-warning" onclick="window['${retryCallbackName}'](${t.id})">重试</button>`;
        html += `</td></tr>`;
    });
    html += `</tbody></table>`;
    container.innerHTML = html;
}

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

function renderPagination(containerId, currentPage, totalPages, onPageChange) {
    const container = document.getElementById(containerId);
    if (!container || totalPages <= 1) {
        if (container) container.innerHTML = "";
        return;
    }
    let html = '<nav><ul class="pagination pagination-sm mb-0 justify-content-center">';
    html += `<li class="page-item ${currentPage <= 1 ? "disabled" : ""}">
        <a class="page-link" href="#" onclick="${onPageChange}(${currentPage - 1}); return false;">&laquo;</a></li>`;

    const maxVisible = 5;
    let start = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    let end = Math.min(totalPages, start + maxVisible - 1);
    if (end - start < maxVisible - 1) start = Math.max(1, end - maxVisible + 1);

    if (start > 1) {
        html += `<li class="page-item"><a class="page-link" href="#" onclick="${onPageChange}(1); return false;">1</a></li>`;
        if (start > 2) html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
    }
    for (let i = start; i <= end; i++) {
        html += `<li class="page-item ${i === currentPage ? "active" : ""}">
            <a class="page-link" href="#" onclick="${onPageChange}(${i}); return false;">${i}</a></li>`;
    }
    if (end < totalPages) {
        if (end < totalPages - 1) html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
        html += `<li class="page-item"><a class="page-link" href="#" onclick="${onPageChange}(${totalPages}); return false;">${totalPages}</a></li>`;
    }

    html += `<li class="page-item ${currentPage >= totalPages ? "disabled" : ""}">
        <a class="page-link" href="#" onclick="${onPageChange}(${currentPage + 1}); return false;">&raquo;</a></li>`;
    html += '</ul></nav>';
    container.innerHTML = html;
}
