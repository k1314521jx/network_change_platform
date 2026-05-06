// 模块D: 三元组入库

let selectedReviewIds = new Set();

document.addEventListener("DOMContentLoaded", () => {
    checkNeo4jStatus();
    loadApprovedReviews();
    loadImportLogs();
    setInterval(loadImportLogs, 5000);
});

async function checkNeo4jStatus() {
    try {
        const res = await apiGet("/api/neo4j/status");
        const el = document.getElementById("neo4jStatus");
        if (res.code === 0 && res.data && res.data.connected) {
            el.innerHTML = '<span class="text-success"><i class="bi bi-check-circle-fill"></i> 已连接</span>';
            document.getElementById("importBtn").disabled = false;
        } else {
            el.innerHTML = '<span class="text-danger"><i class="bi bi-x-circle-fill"></i> 未连接</span>';
        }
    } catch (e) {
        document.getElementById("neo4jStatus").innerHTML = '<span class="text-danger"><i class="bi bi-x-circle-fill"></i> 连接失败</span>';
    }
}

async function loadApprovedReviews() {
    try {
        const res = await apiGet("/api/review/approved");
        const container = document.getElementById("approvedReviewList");
        if (res.code !== 0 || !res.data || res.data.length === 0) {
            container.innerHTML = '<div class="empty-state"><i class="bi bi-inbox"></i><p>暂无审核通过的数据</p></div>';
            return;
        }
        let html = '<div class="list-group list-group-flush">';
        res.data.forEach((item) => {
            html += `
                <label class="list-group-item">
                    <input class="form-check-input me-1" type="checkbox" value="${item.id}" onchange="toggleSelect(${item.id}, this.checked)">
                    <span>审核ID: #${item.id}</span>
                    <small class="text-muted d-block">三元组任务ID: ${item.triple_task_id} | ${item.reviewer || "-"} | ${formatDateTime(item.review_time)}</small>
                </label>`;
        });
        html += '</div>';
        container.innerHTML = html;
    } catch (e) {
        console.error("加载审核通过列表失败", e);
    }
}

function toggleSelect(reviewId, checked) {
    if (checked) {
        selectedReviewIds.add(reviewId);
    } else {
        selectedReviewIds.delete(reviewId);
    }
}

async function triggerImport() {
    if (selectedReviewIds.size === 0) {
        showToast("请先选择要入库的审核数据", "warning");
        return;
    }
    const btn = document.getElementById("importBtn");
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>入库中...';

    try {
        const res = await apiPost("/api/neo4j/import", {
            review_ids: Array.from(selectedReviewIds),
        });
        if (res.code === 0) {
            showToast(res.message, "success");
            selectedReviewIds.clear();
            loadApprovedReviews();
            loadImportLogs();
        } else {
            showToast(res.message, "error");
        }
    } catch (e) {
        showToast("入库请求失败: " + e.message, "error");
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-cloud-upload"></i> 批量入库';
    }
}

async function loadImportLogs() {
    try {
        const res = await apiGet("/api/neo4j/logs?per_page=50");
        if (res.code !== 0) return;
        const columns = [
            { title: "ID", field: "id" },
            { title: "审核记录ID", field: "triple_review_id" },
            { title: "状态", render: (t) => statusBadge(t.status) },
            { title: "错误信息", render: (t) => t.error_message || "-" },
            { title: "入库时间", render: (t) => formatDateTime(t.created_at) },
        ];
        renderTaskTable("importLogContainer", res.data.items, columns);
    } catch (e) {
        console.error("加载入库日志失败", e);
    }
}
