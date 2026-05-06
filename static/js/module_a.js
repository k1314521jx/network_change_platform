// 模块A: 历史变更方案规则化

let detailModal;
let currentPageA = 1;
let searchFilenameA = "";

document.addEventListener("DOMContentLoaded", () => {
    detailModal = new bootstrap.Modal(document.getElementById("detailModal"));
    setupUpload();
    loadTasks();
    setInterval(() => loadTasks(currentPageA), 5000);
});

function setupUpload() {
    const area = document.getElementById("uploadArea");
    const input = document.getElementById("fileInput");

    area.addEventListener("click", () => input.click());
    area.addEventListener("dragover", (e) => { e.preventDefault(); area.classList.add("dragover"); });
    area.addEventListener("dragleave", () => area.classList.remove("dragover"));
    area.addEventListener("drop", (e) => {
        e.preventDefault();
        area.classList.remove("dragover");
        const file = e.dataTransfer.files[0];
        if (file) uploadFile(file);
    });
    input.addEventListener("change", () => {
        if (input.files[0]) uploadFile(input.files[0]);
    });
}

async function uploadFile(file) {
    const progress = document.getElementById("uploadProgress");
    progress.style.display = "block";
    const formData = new FormData();
    formData.append("file", file);

    try {
        const res = await apiUpload("/api/rule/upload", formData);
        progress.style.display = "none";
        if (res.code === 0) {
            showToast("上传成功，任务已创建", "success");
            currentPageA = 1;
            loadTasks();
        } else {
            showToast(res.message || "上传失败", "error");
        }
    } catch (e) {
        progress.style.display = "none";
        showToast("上传失败: " + e.message, "error");
    } finally {
        document.getElementById("fileInput").value = "";
    }
}

window.searchTasks = function() {
    searchFilenameA = document.getElementById("searchFilename").value.trim();
    currentPageA = 1;
    loadTasks();
};

window.goToPageA = function(page) {
    if (page < 1) return;
    currentPageA = page;
    loadTasks(page);
};

async function loadTasks(page) {
    page = page || currentPageA;
    try {
        let url = `/api/rule/tasks?page=${page}&per_page=15`;
        if (searchFilenameA) url += `&filename=${encodeURIComponent(searchFilenameA)}`;
        const res = await apiGet(url);
        if (res.code !== 0) return;

        const columns = [
            { title: "ID", field: "id" },
            { title: "文件名", field: "filename" },
            { title: "状态", render: (t) => statusBadge(t.status) },
            { title: "创建时间", render: (t) => formatDateTime(t.created_at) },
        ];
        renderTaskTable("taskListContainer", res.data.items, columns, "viewDetail", "retryTask");
        renderPagination("taskPagination", res.data.page, res.data.total_pages, "goToPageA");
    } catch (e) {
        console.error("加载任务列表失败", e);
    }
}

window.viewDetail = async function(taskId) {
    try {
        const res = await apiGet(`/api/rule/tasks/${taskId}`);
        if (res.code !== 0) { showToast(res.message, "error"); return; }
        const t = res.data;
        document.getElementById("detailFilename").textContent = t.filename;
        document.getElementById("detailStatus").innerHTML = statusBadge(t.status);
        document.getElementById("detailTime").textContent = formatDateTime(t.created_at);
        document.getElementById("detailJson").textContent = JSON.stringify(t.extracted_json, null, 2);
        detailModal.show();
    } catch (e) {
        showToast("获取详情失败", "error");
    }
};

window.retryTask = async function(taskId) {
    try {
        const res = await apiPost(`/api/rule/tasks/${taskId}/retry`);
        if (res.code === 0) {
            showToast("重试已触发", "success");
            loadTasks();
        } else {
            showToast(res.message, "error");
        }
    } catch (e) {
        showToast("重试失败", "error");
    }
};
