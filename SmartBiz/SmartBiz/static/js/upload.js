/* ==========================================================================
   SmartBiz AI - Drag & Drop File Upload, Zero % Reset & AI Prediction Studio
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    initDragAndDropUpload();
    initResetDataButtons();
});

function initResetDataButtons() {
    const resetModalBtn = document.getElementById('resetDataToZeroBtn');
    const resetTopBtn = document.getElementById('topResetDataBtn');
    
    [resetModalBtn, resetTopBtn].forEach(btn => {
        if (!btn) return;
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            if (!confirm("Are you sure you want to clear all demo data? This will reset your dashboard analytics, revenue, and charts to 0% so you can start fresh with your business files.")) {
                return;
            }
            
            const originalText = btn.innerHTML;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Clearing...';
            btn.disabled = true;
            
            try {
                const res = await fetch('/api/data/reset', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' }
                });
                const data = await res.json();
                
                if (data.status === 'success') {
                    if (typeof showToast === 'function') {
                        showToast(data.message, 'success');
                    } else {
                        alert(data.message);
                    }
                    
                    // Update modal status badge
                    const statusSpan = document.getElementById('dataLoadedStatus');
                    if (statusSpan) {
                        statusSpan.innerHTML = '<i class="fas fa-database me-2"></i>Current Mode: 0% / No Business Files Loaded (Clean Slate)';
                        statusSpan.classList.remove('text-primary');
                        statusSpan.classList.add('text-danger');
                    }
                    
                    // Reset KPI values on page if visible
                    document.querySelectorAll('.kpi-value').forEach(el => {
                        if (el.textContent.includes('$')) el.textContent = '$0.00';
                        else if (el.textContent.includes('%')) el.textContent = '0.0%';
                        else el.textContent = '0';
                    });
                    
                    // Reload Chart.js graphs to show zero / empty state
                    if (typeof fetchDashboardData === 'function') {
                        fetchDashboardData('all');
                    } else {
                        setTimeout(() => window.location.reload(), 1500);
                    }
                } else {
                    alert('Error clearing data: ' + data.message);
                }
            } catch (err) {
                console.error('Reset error:', err);
                alert('An error occurred while resetting data.');
            } finally {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        });
    });
}

function initDragAndDropUpload() {
    const dropZone = document.getElementById('fileDropZone');
    const fileInput = document.getElementById('uploadFileInput');
    const previewContainer = document.getElementById('uploadPreviewContainer');
    const previewTable = document.getElementById('uploadPreviewTable');
    const submitBtn = document.getElementById('uploadSubmitBtn');
    const uploadForm = document.getElementById('fileUploadForm');
    
    if (!dropZone || !fileInput) return;
    
    // Highlight drop zone on drag over
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.add('border-primary', 'bg-primary', 'bg-opacity-10');
        }, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove('border-primary', 'bg-primary', 'bg-opacity-10');
        }, false);
    });
    
    // Handle drop
    dropZone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            handleFileSelection(files[0]);
        }
    });
    
    // Handle manual click select
    dropZone.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            handleFileSelection(fileInput.files[0]);
        }
    });
    
    function handleFileSelection(file) {
        const fileNameSpan = document.getElementById('selectedFileName');
        if (fileNameSpan) fileNameSpan.textContent = `Selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
        
        if (submitBtn) submitBtn.disabled = false;
        
        // Hide previous AI predictions on new file select
        const aiSection = document.getElementById('uploadAiPredictionSection');
        if (aiSection) aiSection.style.display = 'none';
        
        // Preview CSV file client-side
        if (file.name.endsWith('.csv') && previewContainer && previewTable) {
            const reader = new FileReader();
            reader.onload = function(e) {
                const content = e.target.result;
                const rows = content.split('\n').filter(r => r.trim().length > 0).slice(0, 6);
                
                if (rows.length > 0) {
                    let html = '<thead><tr>';
                    const headers = rows[0].split(',');
                    headers.forEach(h => html += `<th>${h.replace(/["']/g, '').trim()}</th>`);
                    html += '</tr></thead><tbody>';
                    
                    for (let i = 1; i < rows.length; i++) {
                        html += '<tr>';
                        const cols = rows[i].split(',');
                        cols.forEach(c => html += `<td>${c.replace(/["']/g, '').trim()}</td>`);
                        html += '</tr>';
                    }
                    html += '</tbody>';
                    
                    previewTable.innerHTML = html;
                    previewContainer.style.display = 'block';
                    if (typeof showToast === 'function') showToast(`Loaded preview of ${file.name}`, 'info');
                }
            };
            reader.readAsText(file);
        } else {
            if (previewContainer) previewContainer.style.display = 'none';
        }
    }
    
    // AJAX Form submission with progress bar & AI Prediction Studio
    if (uploadForm) {
        uploadForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            if (!fileInput.files || fileInput.files.length === 0) {
                alert("Please select a file first!");
                return;
            }
            
            const progressSection = document.getElementById('uploadProgressSection');
            const progressBar = document.getElementById('uploadProgressBar');
            const progressPct = document.getElementById('uploadProgressPct');
            const progressLabel = document.getElementById('uploadProgressLabel');
            const aiSection = document.getElementById('uploadAiPredictionSection');
            
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Ingesting Records...';
            }
            
            if (progressSection) {
                progressSection.style.display = 'block';
                progressBar.style.width = '15%';
                progressPct.textContent = '15%';
                progressLabel.innerHTML = '<i class="fas fa-spinner fa-spin me-2 text-primary"></i>Reading spreadsheet via Pandas...';
            }
            
            // Simulate staged progress
            const pInterval = setInterval(() => {
                let currentW = parseInt(progressBar.style.width) || 15;
                if (currentW < 85) {
                    currentW += Math.floor(Math.random() * 20) + 10;
                    if (currentW > 85) currentW = 85;
                    progressBar.style.width = currentW + '%';
                    progressPct.textContent = currentW + '%';
                    if (currentW > 50) {
                        progressLabel.innerHTML = '<i class="fas fa-brain fa-spin me-2 text-warning"></i>Synthesizing AI Growth Predictions...';
                    }
                }
            }, 350);
            
            const formData = new FormData(uploadForm);
            
            try {
                const res = await fetch('/upload', {
                    method: 'POST',
                    body: formData,
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                });
                
                clearInterval(pInterval);
                const data = await res.json();
                
                if (data.status === 'success') {
                    if (progressBar) {
                        progressBar.style.width = '100%';
                        progressBar.classList.remove('progress-bar-animated');
                        progressBar.classList.add('bg-success');
                        progressPct.textContent = '100%';
                        progressLabel.innerHTML = '<i class="fas fa-check-circle me-2 text-success"></i>Import & AI Analytics Complete!';
                    }
                    
                    if (typeof showToast === 'function') {
                        showToast(data.message, 'success');
                    }
                    
                    // Update Status Badge
                    const statusSpan = document.getElementById('dataLoadedStatus');
                    if (statusSpan) {
                        statusSpan.innerHTML = `<i class="fas fa-check-double me-2"></i>Current Mode: Custom Business Files Active (${data.records_imported} records)`;
                        statusSpan.classList.remove('text-danger', 'text-secondary');
                        statusSpan.classList.add('text-success');
                    }
                    
                    // Display AI Predictions Studio
                    if (aiSection && data.ai_predictions) {
                        document.getElementById('aiPredictionSummary').textContent = data.ai_predictions.summary || '';
                        document.getElementById('aiPredictedGrowth').textContent = data.ai_predictions.predicted_growth || '+24.5%';
                        document.getElementById('aiTopOpportunity').textContent = data.ai_predictions.top_opportunity || 'High velocity detected in top SKU.';
                        document.getElementById('aiKeyPrediction').textContent = data.ai_predictions.key_prediction || '';
                        aiSection.style.display = 'block';
                        
                        // Scroll smoothly to AI section inside modal
                        aiSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    }
                    
                    // Refresh background dashboard chart visualizations
                    if (typeof fetchChartData === 'function') {
                        fetchChartData('all');
                    }
                    
                    // Automatically refresh dashboard after 3.5s so all 12 KPI cards and data tables reflect the uploaded business data!
                    if (window.location.pathname === '/' || window.location.pathname.includes('dashboard')) {
                        setTimeout(() => {
                            window.location.reload();
                        }, 3500);
                    }
                    
                } else {
                    alert('Error: ' + (data.message || 'Failed to upload file'));
                    if (progressSection) progressSection.style.display = 'none';
                }
            } catch (err) {
                clearInterval(pInterval);
                console.error('Upload error:', err);
                alert('An error occurred during file upload and analysis.');
                if (progressSection) progressSection.style.display = 'none';
            } finally {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '<i class="fas fa-database me-2"></i> Confirm & Import Records';
                }
            }
        });
    }
}
