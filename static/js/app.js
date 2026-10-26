// Auto-Enrichment Data System - Frontend Application Logic

// Multi-tenant Session Isolation: Setiap browser memiliki ID unik yang disimpan di LocalStorage
function getSessionId() {
    let sid = localStorage.getItem('nasdem_user_session_id');
    if (!sid) {
        sid = 'sess_' + Math.random().toString(36).substring(2, 10) + '_' + Date.now();
        localStorage.setItem('nasdem_user_session_id', sid);
    }
    return sid;
}

// Fetch Interceptor: Otomatis menyematkan header X-Session-Id pada semua panggilan API
const _nativeFetch = window.fetch;
window.fetch = function(url, options = {}) {
    options = options || {};
    options.headers = options.headers || {};
    const sid = getSessionId();
    if (options.headers instanceof Headers) {
        options.headers.set('X-Session-Id', sid);
    } else if (Array.isArray(options.headers)) {
        options.headers.push(['X-Session-Id', sid]);
    } else {
        options.headers['X-Session-Id'] = sid;
    }
    return _nativeFetch(url, options);
};

const state = {
    currentTab: 'matched',
    page: 1,
    limit: 15,
    search: '',
    dpd: '',
    hasMaster: false,
    hasTarget: false,
    hasProcessed: false,
    masterFilename: '',
    targetFilename: '',
    masterRows: 0,
    targetRows: 0,
    matchedCount: 0,
    unmatchedCount: 0
};

// DOM Elements
const el = {
    btnResetData: document.getElementById('btn-reset-data'),
    btnRunProcess: document.getElementById('btn-run-process'),
    btnExportExcel: document.getElementById('btn-export-excel'),

    btnDeleteMaster: document.getElementById('btn-delete-master'),
    btnDeleteTarget: document.getElementById('btn-delete-target'),

    masterInput: document.getElementById('master-input'),
    targetInput: document.getElementById('target-input'),

    masterDropzone: document.getElementById('master-dropzone'),
    targetDropzone: document.getElementById('target-dropzone'),
    masterDropText: document.getElementById('master-drop-text'),
    targetDropText: document.getElementById('target-drop-text'),
    masterStatus: document.getElementById('master-file-status'),
    targetStatus: document.getElementById('target-file-status'),
    masterCount: document.getElementById('master-count'),
    targetCount: document.getElementById('target-count'),
    kpiGrid: document.getElementById('kpi-grid'),
    kpiTotal: document.getElementById('kpi-total'),
    kpiMatched: document.getElementById('kpi-matched'),
    kpiUnmatched: document.getElementById('kpi-unmatched'),
    kpiRate: document.getElementById('kpi-rate'),
    kpiTime: document.getElementById('kpi-time'),
    tabBtns: document.querySelectorAll('.tab-btn'),
    tableSearch: document.getElementById('table-search'),
    clearSearch: document.getElementById('clear-search'),
    dpdFilter: document.getElementById('dpd-filter'),
    limitSelect: document.getElementById('limit-select'),
    tableLoading: document.getElementById('table-loading'),
    tableEmpty: document.getElementById('table-empty'),
    dataTable: document.getElementById('data-table'),
    tableHead: document.getElementById('table-head'),
    tableBody: document.getElementById('table-body'),
    paginationBar: document.getElementById('pagination-bar'),
    paginationInfo: document.getElementById('pagination-info'),
    pageDisplay: document.getElementById('page-display'),
    btnPageFirst: document.getElementById('btn-page-first'),
    btnPagePrev: document.getElementById('btn-page-prev'),
    btnPageNext: document.getElementById('btn-page-next'),
    btnPageLast: document.getElementById('btn-page-last'),
    exportModal: document.getElementById('export-modal'),
    modalCloseBtn: document.getElementById('modal-close-btn'),
    modalCloseFooter: document.getElementById('modal-close-footer'),
    toastContainer: document.getElementById('toast-container'),
    countBadgeMatched: document.getElementById('count-badge-matched'),
    countBadgeUnmatched: document.getElementById('count-badge-unmatched'),
    countBadgeTarget: document.getElementById('count-badge-target'),
    countBadgeMaster: document.getElementById('count-badge-master')
};

// Toast notification helper
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    el.toastContainer.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

// Debounce helper
function debounce(func, delay = 300) {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => func(...args), delay);
    };
}

// Initialize Application
async function init() {
    setupEventListeners();
    await checkServerStatus();
}

// Check initial status
async function checkServerStatus() {
    try {
        const res = await fetch('/api/status');
        const data = await res.json();
        
        state.hasMaster = data.has_master;
        state.hasTarget = data.has_target;
        state.hasProcessed = data.has_processed;
        state.masterFilename = data.master_filename || '';
        state.targetFilename = data.target_filename || '';
        state.masterRows = data.master_rows;
        state.targetRows = data.target_rows;

        updateUploadUI();

        if (data.summary) {
            updateKPICards(data.summary);
            fetchPreview();
        } else if (state.hasTarget) {
            state.currentTab = 'target';
            updateActiveTabUI();
            fetchPreview();
        }
    } catch (err) {
        console.error("Status check failed", err);
    }
}

function updateUploadUI() {
    if (state.hasMaster) {
        el.masterStatus.textContent = state.masterFilename ? `${state.masterFilename}` : 'File Siap Digunakan';
        el.masterStatus.className = 'file-status active';
        el.masterDropText.textContent = `File Master: ${state.masterFilename || 'Termuat'}`;
        el.masterCount.textContent = `${state.masterRows.toLocaleString()} baris data`;
        el.countBadgeMaster.textContent = state.masterRows;
        if (el.btnDeleteMaster) el.btnDeleteMaster.style.display = 'inline-flex';
    } else {
        el.masterStatus.textContent = 'Belum ada file';
        el.masterStatus.className = 'file-status';
        el.masterDropText.textContent = 'Klik atau seret file Excel/CSV Master ke sini';
        el.masterCount.textContent = '0 baris data';
        el.countBadgeMaster.textContent = '0';
        if (el.btnDeleteMaster) el.btnDeleteMaster.style.display = 'none';
    }
    
    if (state.hasTarget) {
        el.targetStatus.textContent = state.targetFilename ? `${state.targetFilename}` : 'File Siap Digunakan';
        el.targetStatus.className = 'file-status active';
        el.targetDropText.textContent = `File Target: ${state.targetFilename || 'Termuat'}`;
        el.targetCount.textContent = `${state.targetRows.toLocaleString()} baris data`;
        el.countBadgeTarget.textContent = state.targetRows;
        if (el.btnDeleteTarget) el.btnDeleteTarget.style.display = 'inline-flex';
    } else {
        el.targetStatus.textContent = 'Belum ada file';
        el.targetStatus.className = 'file-status';
        el.targetDropText.textContent = 'Klik atau seret file Excel/CSV Target ke sini';
        el.targetCount.textContent = '0 baris data';
        el.countBadgeTarget.textContent = '0';
        if (el.btnDeleteTarget) el.btnDeleteTarget.style.display = 'none';
    }

    el.btnRunProcess.disabled = !(state.hasMaster && state.hasTarget);
    el.btnExportExcel.disabled = !state.hasProcessed;
}


function updateKPICards(summary) {
    el.kpiGrid.style.display = 'grid';
    el.kpiTotal.textContent = summary.total_target.toLocaleString();
    el.kpiMatched.textContent = summary.matched_count.toLocaleString();
    el.kpiUnmatched.textContent = summary.unmatched_count.toLocaleString();
    el.kpiRate.textContent = `${summary.match_rate_pct}% Tingkat Keberhasilan`;
    el.kpiTime.textContent = `${summary.elapsed_seconds}s`;

    state.matchedCount = summary.matched_count;
    state.unmatchedCount = summary.unmatched_count;
    el.countBadgeMatched.textContent = summary.matched_count;
    el.countBadgeUnmatched.textContent = summary.unmatched_count;

    el.btnExportExcel.disabled = false;
}

// Fetch preview data for active tab
async function fetchPreview() {
    el.tableLoading.style.display = 'flex';
    
    try {
        const params = new URLSearchParams({
            dataset: state.currentTab,
            page: state.page,
            limit: state.limit,
            search: state.search,
            dpd: state.dpd
        });

        const res = await fetch(`/api/preview?${params}`);
        const data = await res.json();

        // Update dropdown DPD list jika tersedia
        if (data.dpd_list && data.dpd_list.length > 0) {
            updateDpdDropdown(data.dpd_list);
        }

        renderTable(data);
    } catch (err) {
        console.error("Preview failed", err);
        showToast("Gagal memuat pratinjau tabel", "danger");
    } finally {
        el.tableLoading.style.display = 'none';
    }
}

function updateDpdDropdown(dpdList) {
    const currentVal = el.dpdFilter.value;
    el.dpdFilter.innerHTML = '<option value="">Semua DPD / Kabupaten</option>';
    dpdList.forEach(dpd => {
        const opt = document.createElement('option');
        opt.value = dpd;
        opt.textContent = dpd;
        if (dpd === currentVal) opt.selected = true;
        el.dpdFilter.appendChild(opt);
    });
}

// Render data into table
function renderTable(data) {
    const { columns, rows, total_rows, page, total_pages } = data;

    if (!columns || columns.length === 0 || rows.length === 0) {
        el.dataTable.style.display = 'none';
        el.paginationBar.style.display = 'none';
        el.tableEmpty.style.display = 'flex';
        return;
    }

    el.tableEmpty.style.display = 'none';
    el.dataTable.style.display = 'table';
    el.paginationBar.style.display = 'flex';

    // 1. Render Table Head (Filter out internal columns like _status)
    const visibleCols = columns.filter(c => c !== '_status');
    
    el.tableHead.innerHTML = `
        <tr>
            <th style="width: 50px; text-align: center;">NO</th>
            ${visibleCols.map(c => `<th>${formatHeaderTitle(c)}</th>`).join('')}
        </tr>
    `;

    // 2. Render Table Body
    const startIdx = (page - 1) * state.limit;
    el.tableBody.innerHTML = rows.map((row, idx) => {
        return `
            <tr>
                <td style="text-align: center; color: var(--text-muted);">${startIdx + idx + 1}</td>
                ${visibleCols.map(c => renderCell(c, row[c], row)).join('')}
            </tr>
        `;
    }).join('');

    // 3. Update Pagination
    const endCount = Math.min(startIdx + rows.length, total_rows);
    el.paginationInfo.textContent = `Menampilkan ${startIdx + 1} - ${endCount} dari ${total_rows.toLocaleString()} data`;
    el.pageDisplay.textContent = `${page} / ${total_pages || 1}`;
    
    el.btnPageFirst.disabled = page <= 1;
    el.btnPagePrev.disabled = page <= 1;
    el.btnPageNext.disabled = page >= total_pages;
    el.btnPageLast.disabled = page >= total_pages;
}

function formatHeaderTitle(colName) {
    if (colName === '_kolom_diperkaya') return 'DATA DIPERKAYA';
    if (colName === '_metode_match') return 'METODE COCOK';
    if (colName === 'Keterangan_Gagal') return 'ALASAN BELUM COCOK';
    return colName.replace(/_/g, ' ').toUpperCase();
}

function renderCell(colName, val, row) {
    const text = val === null || val === undefined ? '' : String(val).trim();
    
    // NIK styling
    if (colName.toLowerCase().includes('nik') || colName.toLowerCase().includes('ktp')) {
        return `<td class="cell-nik">${text || '<span style="color:var(--text-muted)">-</span>'}</td>`;
    }
    
    // Alasan Gagal badge
    if (colName === 'Keterangan_Gagal') {
        return `<td><span class="badge-reason">${text}</span></td>`;
    }

    // Info kolom yang berhasil diperkaya
    if (colName === '_kolom_diperkaya') {
        return `<td><span class="badge-enriched">⚡ ${text}</span></td>`;
    }

    // Metode Pencocokan badge
    if (colName === '_metode_match') {
        return `<td><span class="badge-enriched" style="background: rgba(14, 165, 233, 0.15); color: #38bdf8; border-color: rgba(14, 165, 233, 0.3);">🎯 ${text}</span></td>`;
    }


    // Highlight jika cell ini adalah hasil penambahan dari master pada tab matched
    const enrichedList = (row['_kolom_diperkaya'] || '').split(',').map(s => s.trim().toLowerCase());
    if (state.currentTab === 'matched' && enrichedList.includes(colName.toLowerCase()) && text) {
        return `<td class="cell-highlight">${text}</td>`;
    }

    return `<td>${text || '<span style="color:var(--text-muted)">-</span>'}</td>`;
}

function updateActiveTabUI() {
    el.tabBtns.forEach(btn => {
        if (btn.dataset.tab === state.currentTab) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}

// Event Listeners Setup
function setupEventListeners() {
    // 1. Reset Data Real
    if (el.btnResetData) {
        el.btnResetData.addEventListener('click', async () => {
            if (!confirm("Apakah Anda yakin ingin mereset dan mengosongkan semua data yang termuat?")) {
                return;
            }

            el.btnResetData.disabled = true;
            el.btnResetData.textContent = '⏳ Mengosongkan...';
            
            try {
                const res = await fetch('/api/reset', { method: 'POST' });
                const data = await res.json();
                
                if (data.success) {
                    showToast(data.message, 'info');
                    state.hasMaster = false;
                    state.hasTarget = false;
                    state.hasProcessed = false;
                    state.masterRows = 0;
                    state.targetRows = 0;
                    state.matchedCount = 0;
                    state.unmatchedCount = 0;

                    // Reset UI dropzones
                    el.masterStatus.textContent = 'Belum ada file';
                    el.masterStatus.className = 'file-status';
                    el.masterDropText.textContent = 'Klik atau seret file Excel/CSV Master ke sini';
                    el.masterCount.textContent = '0 baris data';
                    el.countBadgeMaster.textContent = '0';

                    el.targetStatus.textContent = 'Belum ada file';
                    el.targetStatus.className = 'file-status';
                    el.targetDropText.textContent = 'Klik atau seret file Excel/CSV Target ke sini';
                    el.targetCount.textContent = '0 baris data';
                    el.countBadgeTarget.textContent = '0';

                    el.countBadgeMatched.textContent = '0';
                    el.countBadgeUnmatched.textContent = '0';

                    el.btnRunProcess.disabled = true;
                    el.btnExportExcel.disabled = true;
                    el.kpiGrid.style.display = 'none';

                    // Reset tabel
                    el.dataTable.style.display = 'none';
                    el.paginationBar.style.display = 'none';
                    el.tableEmpty.style.display = 'flex';
                }
            } catch (err) {
                showToast('Terjadi kesalahan saat mereset data', 'danger');
            } finally {
                el.btnResetData.disabled = false;
                el.btnResetData.innerHTML = '<span class="btn-icon">🗑️</span> Reset / Muat Ulang';
            }
        });
    }

    // Hapus File Master
    if (el.btnDeleteMaster) {
        el.btnDeleteMaster.addEventListener('click', async (e) => {
            e.stopPropagation();
            if (!confirm(`Hapus file Master (${state.masterFilename || 'saat ini'})?`)) return;

            try {
                const res = await fetch('/api/delete-file', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ type: 'master' })
                });
                const data = await res.json();
                if (data.success) {
                    showToast(data.message, 'info');
                    state.hasMaster = false;
                    state.masterFilename = '';
                    state.masterRows = 0;
                    state.hasProcessed = false;
                    updateUploadUI();
                    el.kpiGrid.style.display = 'none';
                    el.dataTable.style.display = 'none';
                    el.paginationBar.style.display = 'none';
                    el.tableEmpty.style.display = 'flex';
                }
            } catch (err) {
                showToast('Gagal menghapus file Master', 'danger');
            }
        });
    }

    // Hapus File Target
    if (el.btnDeleteTarget) {
        el.btnDeleteTarget.addEventListener('click', async (e) => {
            e.stopPropagation();
            if (!confirm(`Hapus file Target (${state.targetFilename || 'saat ini'})?`)) return;

            try {
                const res = await fetch('/api/delete-file', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ type: 'target' })
                });
                const data = await res.json();
                if (data.success) {
                    showToast(data.message, 'info');
                    state.hasTarget = false;
                    state.targetFilename = '';
                    state.targetRows = 0;
                    state.hasProcessed = false;
                    updateUploadUI();
                    el.kpiGrid.style.display = 'none';
                    el.dataTable.style.display = 'none';
                    el.paginationBar.style.display = 'none';
                    el.tableEmpty.style.display = 'flex';
                }
            } catch (err) {
                showToast('Gagal menghapus file Target', 'danger');
            }
        });
    }

    // 2. Upload Handlers
    el.masterInput.addEventListener('change', (e) => handleFileUpload(e.target.files[0], 'master'));
    el.targetInput.addEventListener('change', (e) => handleFileUpload(e.target.files[0], 'target'));


    setupDragAndDrop(el.masterDropzone, (file) => handleFileUpload(file, 'master'));
    setupDragAndDrop(el.targetDropzone, (file) => handleFileUpload(file, 'target'));

    // 3. Jalankan Proses Pencocokan
    el.btnRunProcess.addEventListener('click', async () => {
        el.btnRunProcess.disabled = true;
        el.btnRunProcess.innerHTML = '<span class="btn-icon">⏳</span> Memproses Data...';
        
        try {
            const res = await fetch('/api/process', { method: 'POST' });
            const data = await res.json();
            
            if (data.success) {
                state.hasProcessed = true;
                updateKPICards(data.summary);
                showToast(`Pencocokan Selesai! ${data.summary.matched_count} data berhasil terisi (${data.summary.match_rate_pct}%).`, 'success');
                
                // Langsung tampilkan hasil data diperkaya
                state.currentTab = 'matched';
                state.page = 1;
                updateActiveTabUI();
                await fetchPreview();
            } else {
                showToast(data.error || 'Gagal menjalankan proses', 'danger');
            }
        } catch (err) {
            showToast('Terjadi kesalahan sistem saat pemrosesan', 'danger');
        } finally {
            el.btnRunProcess.disabled = false;
            el.btnRunProcess.innerHTML = '<span class="btn-icon">🔄</span> Jalankan Pencocokan Data';
        }
    });

    // 4. Tabs Switching
    el.tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            state.currentTab = btn.dataset.tab;
            state.page = 1;
            updateActiveTabUI();
            fetchPreview();
        });
    });

    // 5. Search & Filters
    el.tableSearch.addEventListener('input', debounce((e) => {
        state.search = e.target.value.trim();
        state.page = 1;
        el.clearSearch.style.display = state.search ? 'block' : 'none';
        fetchPreview();
    }, 250));

    el.clearSearch.addEventListener('click', () => {
        el.tableSearch.value = '';
        state.search = '';
        el.clearSearch.style.display = 'none';
        state.page = 1;
        fetchPreview();
    });

    el.dpdFilter.addEventListener('change', (e) => {
        state.dpd = e.target.value;
        state.page = 1;
        fetchPreview();
    });

    el.limitSelect.addEventListener('change', (e) => {
        state.limit = parseInt(e.target.value);
        state.page = 1;
        fetchPreview();
    });

    // 6. Pagination
    el.btnPageFirst.addEventListener('click', () => { state.page = 1; fetchPreview(); });
    el.btnPagePrev.addEventListener('click', () => { state.page = Math.max(1, state.page - 1); fetchPreview(); });
    el.btnPageNext.addEventListener('click', () => { state.page++; fetchPreview(); });
    el.btnPageLast.addEventListener('click', () => { state.page = 999999; fetchPreview(); });

    // 7. Export Modal Handlers
    el.btnExportExcel.addEventListener('click', async () => {
        el.btnExportExcel.disabled = true;
        el.btnExportExcel.innerHTML = '<span class="btn-icon">⏳</span> Menyiapkan File Excel...';
        
        try {
            const res = await fetch('/api/export', { method: 'POST' });
            const data = await res.json();
            
                // Update download link template asli dan alternatif dengan ID sesi
                const sidParam = `session_id=${encodeURIComponent(getSessionId())}`;
                const templateFn = data.template_filename || (data.files && data.files.template);
                const btnDownloadTemplate = document.getElementById('btn-download-template');
                const btnDownloadSuccess = document.getElementById('btn-download-success');
                const btnDownloadFailed = document.getElementById('btn-download-failed');
                const titleTemplate = document.getElementById('modal-template-title');
                const failedCard = document.getElementById('modal-failed-card');
                
                if (templateFn && btnDownloadTemplate) {
                    btnDownloadTemplate.href = `/api/download/${encodeURIComponent(templateFn)}?${sidParam}`;
                    if (titleTemplate) titleTemplate.textContent = `${templateFn} (Format Asli Lengkap)`;
                }

                if (btnDownloadSuccess) {
                    btnDownloadSuccess.href = `/api/download/Data_Lengkap_Sukses.xlsx?${sidParam}`;
                }

                if (btnDownloadFailed) {
                    btnDownloadFailed.href = `/api/download/Data_Gagal_Match.xlsx?${sidParam}`;
                }

                if (failedCard) {
                    failedCard.style.display = state.unmatchedCount > 0 ? 'flex' : 'none';
                }

                el.exportModal.style.display = 'flex';
                showToast("File Excel siap diunduh!", "success");
            } else {
                showToast(data.error || 'Gagal mengekspor file', 'danger');
            }
        } catch (err) {
            showToast('Terjadi kesalahan ekspor', 'danger');
        } finally {
            el.btnExportExcel.disabled = false;
            el.btnExportExcel.innerHTML = '<span class="btn-icon">💾</span> Konfirmasi & Export Excel';
        }
    });

    el.modalCloseBtn.addEventListener('click', () => el.exportModal.style.display = 'none');
    el.modalCloseFooter.addEventListener('click', () => el.exportModal.style.display = 'none');

    el.exportModal.addEventListener('click', (e) => {
        if (e.target === el.exportModal) el.exportModal.style.display = 'none';
    });
}

// Drag & drop helper
function setupDragAndDrop(dropzone, callback) {
    ['dragenter', 'dragover'].forEach(name => {
        dropzone.addEventListener(name, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add('dragover');
        });
    });
    
    ['dragleave', 'drop'].forEach(name => {
        dropzone.addEventListener(name, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('dragover');
        });
    });

    dropzone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) callback(files[0]);
    });
}

// Handle file upload
async function handleFileUpload(file, type) {
    if (!file) return;

    const formData = new FormData();
    if (type === 'master') {
        formData.append('master_file', file);
    } else {
        formData.append('target_file', file);
    }

    showToast(`Mengunggah file ${file.name}...`, 'info');

    try {
        const res = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();

        if (data.success) {
            showToast(`File ${file.name} berhasil dimuat.`, 'success');
            if (type === 'master') {
                state.hasMaster = true;
                state.masterRows = data.master_rows;
            } else {
                state.hasTarget = true;
                state.targetRows = data.target_rows;
            }
            state.hasProcessed = false;
            updateUploadUI();

            // Set preview ke file yang baru diunggah
            state.currentTab = type;
            state.page = 1;
            updateActiveTabUI();
            fetchPreview();
        } else {
            showToast(data.error || 'Gagal mengunggah file', 'danger');
        }
    } catch (err) {
        showToast('Terjadi kesalahan jaringan saat mengunggah', 'danger');
    }
}

// Boot application when DOM is ready
document.addEventListener('DOMContentLoaded', init);
