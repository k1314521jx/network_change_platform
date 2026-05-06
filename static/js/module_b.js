// 模块B: 规则化转三元组

let tripleDetailModal;
let currentPageB = 1;
let searchFilenameB = "";

document.addEventListener("DOMContentLoaded", () => {
    tripleDetailModal = new bootstrap.Modal(document.getElementById("tripleDetailModal"));
    loadRuleDataOptions();
    loadTripleTasks();
    setInterval(() => loadTripleTasks(currentPageB), 5000);
});

async function loadRuleDataOptions() {
    try {
        const res = await apiGet("/api/rule/tasks/success");
        const select = document.getElementById("ruleDataSelect");
        select.innerHTML = '<option value="">-- 请选择 --</option>';
        if (res.code === 0 && res.data) {
            res.data.forEach((t) => {
                select.innerHTML += `<option value="${t.id}">#${t.id} - ${t.filename} (${formatDateTime(t.created_at)})</option>`;
            });
        }
    } catch (e) {
        console.error("加载规则数据失败", e);
    }
}

async function triggerConvert() {
    const ruleTaskId = document.getElementById("ruleDataSelect").value;
    if (!ruleTaskId) { showToast("请先选择规则化数据", "warning"); return; }

    const btn = document.getElementById("convertBtn");
    const statusEl = document.getElementById("convertStatus");
    btn.disabled = true;
    statusEl.style.display = "block";

    try {
        const model = document.getElementById("modelSelect").value;
        const res = await apiPost("/api/triple/convert", { rule_task_id: parseInt(ruleTaskId), model: model });
        if (res.code === 0) {
            showToast("转换任务已创建", "success");
            currentPageB = 1;
            loadTripleTasks();
        } else {
            showToast(res.message, "error");
        }
    } catch (e) {
        showToast("请求失败: " + e.message, "error");
    } finally {
        btn.disabled = false;
        statusEl.style.display = "none";
    }
}

window.searchTripleTasks = function() {
    searchFilenameB = document.getElementById("searchTripleFilename").value.trim();
    currentPageB = 1;
    loadTripleTasks();
};

window.goToPageB = function(page) {
    if (page < 1) return;
    currentPageB = page;
    loadTripleTasks(page);
};

async function loadTripleTasks(page) {
    page = page || currentPageB;
    try {
        let url = `/api/triple/tasks?page=${page}&per_page=15`;
        if (searchFilenameB) url += `&filename=${encodeURIComponent(searchFilenameB)}`;
        const res = await apiGet(url);
        if (res.code !== 0) return;
        const columns = [
            { title: "ID", field: "id" },
            { title: "关联规则ID", field: "rule_task_id" },
            { title: "规则文件名", field: "rule_filename" },
            { title: "状态", render: (t) => statusBadge(t.status) },
            { title: "创建时间", render: (t) => formatDateTime(t.created_at) },
        ];
        renderTaskTable("tripleTaskList", res.data.items, columns, "viewTripleDetail");
        renderPagination("triplePagination", res.data.page, res.data.total_pages, "goToPageB");
    } catch (e) {
        console.error("加载三元组任务失败", e);
    }
}

window.viewTripleDetail = async function(taskId) {
    try {
        const res = await apiGet(`/api/triple/tasks/${taskId}`);
        if (res.code !== 0) { showToast(res.message, "error"); return; }
        const t = res.data;

        document.getElementById("tripleDetailId").textContent = t.id;
        document.getElementById("tripleDetailStatus").innerHTML = statusBadge(t.status);
        document.getElementById("tripleDetailTime").textContent = formatDateTime(t.created_at);
        document.getElementById("detailRawJson").textContent = JSON.stringify(t.triple_json, null, 2);

        const tripleData = t.triple_json || {};

        document.getElementById("detailTable1").innerHTML = buildReadonlyTable(
            tripleData.Table1_Alignment || [],
            ["row_index", "raw_cmd", "raw_rollback", "step_name", "au_name", "role", "entity", "parameters"]
        );

        document.getElementById("detailTable2").innerHTML = buildReadonlyTable(
            tripleData.Table2_Entities_Attributes || [],
            ["id", "label", "name", "properties"]
        );

        document.getElementById("detailTable3").innerHTML = buildReadonlyTable(
            tripleData.Table3_Relations || [],
            ["source_entity", "relation_type", "target_entity", "relation_attributes"]
        );

        document.querySelector("#tripleTabs .nav-link").click();

        tripleDetailModal.show();
    } catch (e) {
        showToast("获取详情失败", "error");
    }
};

function buildReadonlyTable(data, columns) {
    if (!data || data.length === 0) return '<div class="p-3 text-muted">无数据</div>';
    let html = '<table class="table table-sm edit-table"><thead><tr>';
    columns.forEach((c) => { html += `<th>${c}</th>`; });
    html += '</tr></thead><tbody>';
    data.forEach((row) => {
        html += '<tr>';
        columns.forEach((c) => {
            let val = row[c];
            if (typeof val === "object") val = JSON.stringify(val);
            html += `<td>${val !== undefined ? escapeHtml(String(val)) : ""}</td>`;
        });
        html += '</tr>';
    });
    html += '</tbody></table>';
    return html;
}

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}
