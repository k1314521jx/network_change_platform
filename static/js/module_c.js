// 模块C: 三元组审核

let currentTripleTaskId = null;
let currentReviewStatus = null;
let currentTab = "pending";
let pendingReviewAction = null;
let reviewerModal;
let currentEditData = { table1: [], table2: [], table3: [] };
let isReadonly = false;  // 已通过的数据只读

document.addEventListener("DOMContentLoaded", () => {
    reviewerModal = new bootstrap.Modal(document.getElementById("reviewerModal"));
    document.getElementById("confirmReviewBtn").addEventListener("click", doSubmitReview);
    loadPendingList();
    setInterval(() => {
        if (currentTab === "pending") loadPendingList();
    }, 10000);
});

window.switchReviewTab = function(tab) {
    currentTab = tab;
    currentTripleTaskId = null;
    currentEditData = { table1: [], table2: [], table3: [] };
    isReadonly = (tab === "approved");
    document.getElementById("reviewEditor").innerHTML =
        '<div class="empty-state"><i class="bi bi-arrow-left-circle"></i><p>请从左侧列表选择数据</p></div>';
    if (tab === "pending") loadPendingList();
    else if (tab === "approved") loadApprovedList();
    else if (tab === "rejected") loadRejectedList();
};

// ====== 待审核列表 ======
async function loadPendingList() {
    try {
        const res = await apiGet("/api/review/list");
        if (res.code !== 0) return;
        renderList("pendingReviewList", res.data, "pending");
    } catch (e) {
        console.error("加载待审核列表失败", e);
    }
}

// ====== 已通过列表 ======
async function loadApprovedList() {
    try {
        const res = await apiGet("/api/review/approved");
        if (res.code !== 0) return;
        // 需要附带文件名信息
        const items = (res.data || []).map(r => ({
            id: r.triple_task_id,
            review_id: r.id,
            rule_filename: "",
            review_status: "approved",
            reviewer: r.reviewer,
            review_time: r.review_time,
        }));
        renderList("approvedReviewList", items, "approved");
    } catch (e) {
        console.error("加载已通过列表失败", e);
    }
}

// ====== 已驳回列表 ======
async function loadRejectedList() {
    try {
        const res = await apiGet("/api/review/rejected");
        if (res.code !== 0) return;
        const items = (res.data || []).map(r => ({
            id: r.triple_task_id,
            review_id: r.id,
            rule_filename: r.rule_filename || "",
            review_status: "rejected",
            reviewer: r.reviewer,
            review_time: r.review_time,
        }));
        renderList("rejectedReviewList", items, "rejected");
    } catch (e) {
        console.error("加载已驳回列表失败", e);
    }
}

function renderList(containerId, items, type) {
    const container = document.getElementById(containerId);
    if (!items || items.length === 0) {
        container.innerHTML = '<div class="empty-state"><i class="bi bi-inbox"></i><p>暂无数据</p></div>';
        return;
    }
    let html = "";
    items.forEach((item) => {
        const badge = statusBadge(item.review_status, "review");
        const active = item.id === currentTripleTaskId ? "active" : "";
        const label = type === "pending" ? `#${item.id} - ${item.rule_filename}` :
            `#${item.id} | ${item.reviewer || "-"}`;
        html += `
            <a href="#" class="list-group-item list-group-item-action ${active}"
               onclick="window.selectReview(${item.id}, '${item.review_status || 'pending'}'); return false;">
                <div class="d-flex justify-content-between align-items-center">
                    <div class="text-truncate" style="max-width:180px;">${label}</div>
                    ${badge}
                </div>
                <small class="text-muted">${formatDateTime(item.review_time || item.created_at)}</small>
            </a>`;
    });
    container.innerHTML = html;
}

window.selectReview = async function(tripleTaskId, reviewStatus) {
    if (!tripleTaskId || tripleTaskId === "undefined") {
        showToast("无效的任务ID，请刷新页面重试", "error");
        return;
    }
    currentTripleTaskId = tripleTaskId;
    currentReviewStatus = reviewStatus;
    isReadonly = (reviewStatus === "approved");
    try {
        const res = await apiGet(`/api/review/${tripleTaskId}`);
        if (res.code !== 0) { showToast(res.message, "error"); return; }

        currentEditData = {
            table1: res.data.table1 || [],
            table2: res.data.table2 || [],
            table3: res.data.table3 || [],
        };
        renderEditor();
        // 刷新当前 tab 列表
        if (currentTab === "pending") loadPendingList();
        else if (currentTab === "approved") loadApprovedList();
        else if (currentTab === "rejected") loadRejectedList();
    } catch (e) {
        console.error("加载审核数据失败", e);
        showToast("加载审核数据失败: " + (e.message || e), "error");
    }
};

function renderEditor() {
    const container = document.getElementById("reviewEditor");
    const roAttr = isReadonly ? "" : 'contenteditable="true"';
    const statusLabel = isReadonly
        ? '<span class="badge review-approved ms-2">已通过（只读）</span>'
        : (currentReviewStatus === "rejected"
            ? '<span class="badge review-rejected ms-2">已驳回（可编辑）</span>'
            : '<span class="badge bg-secondary ms-2">待审核</span>');

    container.innerHTML = `
        <div class="d-flex align-items-center mb-3">
            <h6 class="mb-0">三元组数据 #${currentTripleTaskId}</h6>
            ${statusLabel}
        </div>
        <ul class="nav nav-tabs sheet-tabs mb-3" id="editSheetTabs">
            <li class="nav-item"><a class="nav-link active" data-bs-toggle="tab" href="#sheet1">Table1_Alignment (${currentEditData.table1.length})</a></li>
            <li class="nav-item"><a class="nav-link" data-bs-toggle="tab" href="#sheet2">Table2_Entities_Attributes (${currentEditData.table2.length})</a></li>
            <li class="nav-item"><a class="nav-link" data-bs-toggle="tab" href="#sheet3">Table3_Relations (${currentEditData.table3.length})</a></li>
        </ul>
        <div class="tab-content">
            <div class="tab-pane fade show active" id="sheet1">
                ${buildEditTable("table1", currentEditData.table1, ["row_index", "raw_cmd", "raw_rollback", "step_name", "au_name", "role", "entity", "parameters"])}
            </div>
            <div class="tab-pane fade" id="sheet2">
                ${buildEditTable("table2", currentEditData.table2, ["id", "label", "name", "properties"])}
            </div>
            <div class="tab-pane fade" id="sheet3">
                ${buildEditTable("table3", currentEditData.table3, ["source_entity", "relation_type", "target_entity", "relation_attributes"])}
            </div>
        </div>
    `;
}

function buildEditTable(tableKey, data, columns) {
    const roAttr = isReadonly ? "" : 'contenteditable="true"';
    if (!data || data.length === 0) {
        if (isReadonly) return '<p class="text-muted">暂无数据</p>';
        return `
            <p class="text-muted">暂无数据</p>
            <button class="btn btn-sm btn-outline-primary btn-add-row" onclick="window.addRow('${tableKey}', ${JSON.stringify(columns).replace(/"/g, '&quot;')})">+ 新增行</button>`;
    }
    let html = "";
    if (!isReadonly) {
        html += `<button class="btn btn-sm btn-outline-primary btn-add-row mb-2" onclick="window.addRow('${tableKey}', ${JSON.stringify(columns).replace(/"/g, '&quot;')})">+ 新增行</button>`;
    }
    html += `<div class="edit-table-container"><table class="table table-sm edit-table"><thead><tr>`;
    columns.forEach((c) => { html += `<th>${c}</th>`; });
    if (!isReadonly) html += '<th style="width:60px;">操作</th>';
    html += '</tr></thead><tbody>';

    data.forEach((row, rowIdx) => {
        html += `<tr data-row="${rowIdx}">`;
        columns.forEach((col) => {
            let val = row[col];
            if (typeof val === "object") val = JSON.stringify(val);
            html += `<td ${roAttr} data-col="${col}" data-row="${rowIdx}" data-table="${tableKey}">${val !== undefined && val !== null ? escapeHtml(String(val)) : ""}</td>`;
        });
        if (!isReadonly) {
            html += `<td><button class="btn btn-sm btn-outline-danger btn-add-row" onclick="window.deleteRow('${tableKey}', ${rowIdx})" title="删除行"><i class="bi bi-trash"></i></button></td>`;
        }
        html += '</tr>';
    });
    html += '</tbody></table></div>';
    return html;
}

window.addRow = function(tableKey, columns) {
    const newRow = {};
    columns.forEach((c) => { newRow[c] = ""; });
    currentEditData[tableKey].push(newRow);
    renderEditor();
    showToast("已添加新行，请编辑后提交", "success");
};

window.deleteRow = function(tableKey, rowIdx) {
    if (!confirm("确定删除该行？")) return;
    currentEditData[tableKey].splice(rowIdx, 1);
    renderEditor();
    showToast("行已删除（点击审核通过/驳回保存）", "warning");
};

// 监听可编辑单元格变化
document.addEventListener("blur", (e) => {
    const cell = e.target.closest("td[contenteditable]");
    if (!cell) return;
    const tableKey = cell.dataset.table;
    const rowIdx = parseInt(cell.dataset.row);
    const col = cell.dataset.col;
    const newValue = cell.textContent.trim();
    if (tableKey && !isNaN(rowIdx) && col && currentEditData[tableKey] && currentEditData[tableKey][rowIdx]) {
        try {
            currentEditData[tableKey][rowIdx][col] = JSON.parse(newValue);
        } catch {
            currentEditData[tableKey][rowIdx][col] = newValue;
        }
    }
}, true);

window.submitReview = function(status) {
    if (!currentTripleTaskId) {
        showToast("请先选择待审核数据", "warning");
        return;
    }
    if (isReadonly) {
        showToast("已通过的数据不可再次审核", "warning");
        return;
    }
    pendingReviewAction = status;
    const textEl = document.getElementById("reviewActionText");
    textEl.textContent = status === "approved" ? "确认审核通过？" : "确认驳回？";
    document.getElementById("reviewerName").value = "";
    reviewerModal.show();
};

async function doSubmitReview() {
    const reviewer = document.getElementById("reviewerName").value.trim();
    if (!reviewer) { showToast("请输入审核人姓名", "warning"); return; }

    try {
        const res = await apiPost(`/api/review/${currentTripleTaskId}/submit`, {
            table1: currentEditData.table1,
            table2: currentEditData.table2,
            table3: currentEditData.table3,
            review_status: pendingReviewAction,
            reviewer: reviewer,
        });
        if (res.code === 0) {
            showToast("审核提交成功", "success");
            reviewerModal.hide();
            currentTripleTaskId = null;
            currentEditData = { table1: [], table2: [], table3: [] };
            document.getElementById("reviewEditor").innerHTML =
                '<div class="empty-state"><i class="bi bi-arrow-left-circle"></i><p>请从左侧列表选择数据</p></div>';
            loadPendingList();
        } else {
            showToast(res.message, "error");
        }
    } catch (e) {
        showToast("提交失败: " + e.message, "error");
    }
}
