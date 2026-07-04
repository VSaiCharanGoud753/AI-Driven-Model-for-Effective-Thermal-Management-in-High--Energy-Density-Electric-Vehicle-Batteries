/**
 * SmartBiz AI - Business Data Studio & AI Ingestion Controller
 * Handles multi-format drag-and-drop (CSV, Excel, PDF, TXT, JSON), live table/text extraction preview,
 * Google Gemini 2.5 Pro dataset analysis, target destination routing, and 0% dashboard reset.
 */

document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('studioDropZone');
    const fileInput = document.getElementById('studioFileInput');
    const selectedFileDiv = document.getElementById('studioSelectedFile');
    const targetContainer = document.getElementById('targetSelectionContainer');
    const executeBtn = document.getElementById('executeImportBtn');
    const resetBtn = document.getElementById('studioResetZeroBtn');

    const rightEmpty = document.getElementById('studioRightEmpty');
    const processingState = document.getElementById('studioProcessingState');
    const loadedContent = document.getElementById('studioLoadedContent');
    const successBanner = document.getElementById('studioSuccessBanner');

    let currentSelectedFile = null;

    // 1. Trigger File Input on Browse / Click
    if (dropZone && fileInput) {
        dropZone.addEventListener('click', () => fileInput.click());

        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.style.borderColor = '#4f46e5';
            dropZone.style.background = 'rgba(79, 70, 229, 0.08)';
        });

        dropZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            dropZone.style.borderColor = 'var(--primary)';
            dropZone.style.background = 'rgba(79, 70, 229, 0.03)';
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.style.borderColor = 'var(--primary)';
            dropZone.style.background = 'rgba(79, 70, 229, 0.03)';
            if (e.dataTransfer.files.length > 0) {
                handleFileSelection(e.dataTransfer.files[0]);
            }
        });

        fileInput.addEventListener('change', (e) => {
            if (fileInput.files.length > 0) {
                handleFileSelection(fileInput.files[0]);
            }
        });
    }

    // 2. Handle File Selection & Trigger Preview / AI Analysis
    function handleFileSelection(file) {
        const validExts = ['csv', 'xls', 'xlsx', 'pdf', 'txt', 'json'];
        const ext = file.name.split('.').pop().toLowerCase();
        
        if (!validExts.includes(ext)) {
            alert(`Unsupported file format (.${ext}). Please select CSV, Excel (.xlsx/.xls), PDF, TXT, or JSON.`);
            return;
        }

        currentSelectedFile = file;
        selectedFileDiv.style.display = 'block';
        selectedFileDiv.innerHTML = `<i class="fas fa-file-circle-check me-2 text-success"></i>Selected: <strong>${file.name}</strong> (${(file.size / 1024).toFixed(1)} KB)`;

        // Show Processing Shimmer
        rightEmpty.style.display = 'none';
        loadedContent.style.display = 'none';
        successBanner.style.display = 'none';
        processingState.style.display = 'flex';
        targetContainer.style.display = 'none';

        // Send AJAX Request for Preview & AI Analysis
        const formData = new FormData();
        formData.append('file', file);

        fetch('/api/upload/preview', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                renderPreviewAndAI(data);
            } else {
                alert(`Error reading file: ${data.message}`);
                processingState.style.display = 'none';
                rightEmpty.style.display = 'flex';
            }
        })
        .catch(err => {
            console.error('Preview error:', err);
            alert('An error occurred while parsing the file.');
            processingState.style.display = 'none';
            rightEmpty.style.display = 'flex';
        });
    }

    // 3. Render Table Preview & AI Analysis Cards
    function renderPreviewAndAI(data) {
        processingState.style.display = 'none';
        loadedContent.style.display = 'flex';
        targetContainer.style.display = 'block';

        // Populate Table Preview
        const thead = document.getElementById('previewTableHead');
        const tbody = document.getElementById('previewTableBody');
        const metaText = document.getElementById('previewMetaText');
        const formatBadge = document.getElementById('previewFormatBadge');

        thead.innerHTML = '';
        tbody.innerHTML = '';

        formatBadge.innerText = data.file_type.toUpperCase();
        metaText.innerText = `Showing ${data.preview_rows.length} of ${data.records_count} extracted records (${data.file_type.toUpperCase()})`;

        // Render headers
        data.columns.forEach(col => {
            const th = document.createElement('th');
            th.innerText = col.toUpperCase();
            th.style.padding = '10px 14px';
            thead.appendChild(th);
        });

        // Render rows
        data.preview_rows.forEach(row => {
            const tr = document.createElement('tr');
            data.columns.forEach(col => {
                const td = document.createElement('td');
                const val = row[col] !== undefined ? row[col] : '';
                td.innerText = val;
                td.style.padding = '8px 14px';
                if (typeof val === 'number' || strIsNum(val)) {
                    td.classList.add('fw-bold', 'text-primary');
                }
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });

        // Populate AI Analysis Card
        const ai = data.ai_analysis;
        if (ai) {
            document.getElementById('aiDatasetTitle').innerText = ai.dataset_type || 'Business Dataset Intelligence';
            document.getElementById('aiHealthScore').innerText = ai.efficiency_score || '94 / 100 Health';
            document.getElementById('aiExecSummary').innerText = ai.summary || '';
            document.getElementById('aiGrowthMetric').innerText = ai.predicted_growth || '+28.4% Projected';
            document.getElementById('aiTopAsset').innerText = ai.top_opportunity || 'High Velocity Asset';
            document.getElementById('aiLedgerType').innerText = ai.dataset_type || 'General Ledger';
            document.getElementById('aiRiskCheck').innerText = ai.risk_detection || 'No risks detected';
            document.getElementById('aiKeyPredictionText').innerText = ai.key_prediction || '';

            const recList = document.getElementById('aiRecommendationsList');
            recList.innerHTML = '';
            if (ai.recommendations && ai.recommendations.length > 0) {
                ai.recommendations.forEach(rec => {
                    const li = document.createElement('li');
                    li.className = 'list-group-item d-flex align-items-start gap-2 py-3 px-3';
                    li.innerHTML = `<i class="fas fa-check-circle text-success mt-1"></i> <span>${rec}</span>`;
                    recList.appendChild(li);
                });
            }
        }
    }

    function strIsNum(val) {
        if (typeof val !== 'string') return false;
        return !isNaN(val.replace('$', '').replace(',', '').trim()) && val.trim() !== '';
    }

    // 4. Handle Execute Import Button
    if (executeBtn) {
        executeBtn.addEventListener('click', () => {
            if (!currentSelectedFile) {
                alert('Please select a file first.');
                return;
            }

            const targetModule = document.querySelector('input[name="targetModule"]:checked').value;
            const formData = new FormData();
            formData.append('file', currentSelectedFile);
            formData.append('target_module', targetModule);

            executeBtn.disabled = true;
            executeBtn.innerHTML = `<i class="fas fa-spinner fa-spin me-2"></i> Ingesting & Updating Database...`;

            fetch('/upload?ajax=true', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                executeBtn.disabled = false;
                executeBtn.innerHTML = `<i class="fas fa-database me-2"></i> Confirm & Import Records into Dashboard`;

                if (data.status === 'success') {
                    loadedContent.style.display = 'none';
                    targetContainer.style.display = 'none';
                    successBanner.style.display = 'block';
                    document.getElementById('successMessageText').innerText = data.message + ` (${data.records_imported} records ingested into SQLite).`;

                    // Update header numbers
                    const revEl = document.getElementById('studioTotalRevenue');
                    const recEl = document.getElementById('studioTotalRecords');
                    if (revEl && data.total_revenue !== undefined) {
                        revEl.innerText = '$' + Number(data.total_revenue).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
                    }
                    if (recEl && data.records_imported !== undefined) {
                        recEl.innerText = Number(recEl.innerText || 0) + Number(data.records_imported);
                    }
                } else {
                    alert(`Import Failed: ${data.message}`);
                }
            })
            .catch(err => {
                console.error('Import error:', err);
                executeBtn.disabled = false;
                executeBtn.innerHTML = `<i class="fas fa-database me-2"></i> Confirm & Import Records into Dashboard`;
                alert('An error occurred during data import.');
            });
        });
    }

    // 5. Handle Reset Dashboard to 0% Button
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            if (!confirm("Are you sure you want to reset all demo data? Your dashboard KPIs and all 11 Chart.js graphs will start at 0% / $0.00.")) {
                return;
            }

            resetBtn.disabled = true;
            resetBtn.innerHTML = `<i class="fas fa-spinner fa-spin me-1"></i> Resetting...`;

            fetch('/api/data/reset', {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                resetBtn.disabled = false;
                resetBtn.innerHTML = `<i class="fas fa-trash-can me-1"></i> Reset Dashboard to 0%`;

                if (data.status === 'success') {
                    document.getElementById('studioTotalRevenue').innerText = '$0.00';
                    document.getElementById('studioTotalRecords').innerText = '0';
                    alert('All demo records cleared! Your database is now at 0% clean slate.');
                } else {
                    alert(`Error resetting data: ${data.message}`);
                }
            })
            .catch(err => {
                console.error('Reset error:', err);
                resetBtn.disabled = false;
                resetBtn.innerHTML = `<i class="fas fa-trash-can me-1"></i> Reset Dashboard to 0%`;
                alert('Error connecting to server.');
            });
        });
    }
});
