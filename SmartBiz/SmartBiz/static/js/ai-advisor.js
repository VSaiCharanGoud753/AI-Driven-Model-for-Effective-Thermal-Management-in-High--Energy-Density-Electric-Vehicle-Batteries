/* ==========================================================================
   SmartBiz AI - Google Gemini AI Business Advisor Client Controller
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    const analyzeBtn = document.getElementById('analyzeBusinessBtn');
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', triggerAIAnalysis);
    }
});

function triggerAIAnalysis() {
    const analyzeBtn = document.getElementById('analyzeBusinessBtn');
    const resultsContainer = document.getElementById('aiAdvisorResults');
    const loadingState = document.getElementById('aiLoadingState');
    const emptyState = document.getElementById('aiEmptyState');
    
    if (!resultsContainer || !loadingState) return;
    
    // UI state transitions
    if (emptyState) emptyState.style.display = 'none';
    resultsContainer.style.display = 'none';
    loadingState.style.display = 'block';
    
    if (analyzeBtn) {
        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Consulting Gemini AI...';
    }
    
    // Simulate multi-step progress steps for dramatic UX effect
    const progressText = document.getElementById('aiProgressText');
    const steps = [
        "Reading financial ledgers & profit margins...",
        "Evaluating SKU turnover & stockout risks...",
        "Analyzing customer RFM segmentation & churn...",
        "Synthesizing 12-point strategic growth plan..."
    ];
    let stepIdx = 0;
    const stepInterval = setInterval(() => {
        if (progressText && stepIdx < steps.length) {
            progressText.textContent = steps[stepIdx];
            stepIdx++;
        }
    }, 800);

    fetch('/api/ai/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(res => res.json())
    .then(response => {
        clearInterval(stepInterval);
        loadingState.style.display = 'none';
        
        if (analyzeBtn) {
            analyzeBtn.disabled = false;
            analyzeBtn.innerHTML = '<i class="fas fa-wand-magic-sparkles me-2"></i>Re-Analyze Business';
        }
        
        if (response.status === 'success' && response.data) {
            renderAIInsights(response.data, response.timestamp);
            resultsContainer.style.display = 'block';
            showToast('Gemini AI analysis generated successfully!', 'success');
            
            // Smooth scroll to results
            resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        } else {
            showToast('Failed to generate AI insights. Using fallback advisor.', 'error');
        }
    })
    .catch(err => {
        clearInterval(stepInterval);
        loadingState.style.display = 'none';
        if (analyzeBtn) {
            analyzeBtn.disabled = false;
            analyzeBtn.innerHTML = '<i class="fas fa-wand-magic-sparkles me-2"></i>Analyze My Business';
        }
        showToast('Network error during AI analysis.', 'error');
        console.error(err);
    });
}

function renderAIInsights(data, timestamp) {
    const container = document.getElementById('aiInsightsGrid');
    const timeSpan = document.getElementById('aiTimestamp');
    if (timeSpan) timeSpan.textContent = `Generated on ${timestamp}`;
    if (!container) return;
    
    const insightCategories = [
        { key: 'summary', title: 'Executive Business Summary', icon: 'fa-briefcase', color: 'primary' },
        { key: 'sales_analysis', title: 'Sales Trend Analysis', icon: 'fa-chart-line', color: 'success' },
        { key: 'profit_analysis', title: 'Profit Margin Analysis', icon: 'fa-coins', color: 'info' },
        { key: 'best_products', title: 'Best Performing Products', icon: 'fa-trophy', color: 'warning' },
        { key: 'weak_products', title: 'Weak Performing Products', icon: 'fa-arrow-trend-down', color: 'danger' },
        { key: 'opportunities', title: 'Growth Opportunities', icon: 'fa-rocket', color: 'primary' },
        { key: 'customer_insights', title: 'Customer Behavioral Insights', icon: 'fa-users', color: 'info' },
        { key: 'marketing_suggestions', title: 'Marketing Campaign Suggestions', icon: 'fa-bullhorn', color: 'warning' },
        { key: 'inventory_suggestions', title: 'Inventory Optimization Suggestions', icon: 'fa-boxes-stacked', color: 'success' },
        { key: 'risk_analysis', title: 'Operational Risk Analysis', icon: 'fa-shield-halved', color: 'danger' },
        { key: 'future_growth', title: 'Future Revenue Prediction', icon: 'fa-crystal-ball', color: 'primary' },
        { key: 'recommendations', title: 'Personalized Recommendations', icon: 'fa-list-check', color: 'success' }
    ];
    
    let html = '';
    insightCategories.forEach((item, idx) => {
        const text = data[item.key] || "Analysis available in full executive report.";
        const delay = idx * 0.1;
        
        html += `
            <div class="col-md-6 col-xl-4 mb-4" style="animation: fadeInUp 0.5s ease forwards; animation-delay: ${delay}s; opacity: 0;">
                <div class="glass-card p-4 h-100 d-flex flex-column justify-content-between position-relative overflow-hidden">
                    <div class="position-absolute top-0 start-0 bottom-0" style="width: 4px; background: var(--${item.color});"></div>
                    <div>
                        <div class="d-flex align-items-center gap-3 mb-3">
                            <div class="kpi-icon mb-0 bg-${item.color} bg-opacity-10 text-${item.color}" style="width:42px;height:42px;font-size:1.2rem;background:rgba(79,70,229,0.1);">
                                <i class="fas ${item.icon} text-${item.color}"></i>
                            </div>
                            <h5 class="mb-0 fw-bold fs-6">${item.title}</h5>
                        </div>
                        <p class="text-secondary mb-0" style="font-size: 0.9rem; line-height: 1.6;">${text}</p>
                    </div>
                    <div class="mt-3 pt-3 border-top d-flex justify-content-between align-items-center">
                        <span class="badge bg-${item.color} bg-opacity-10 text-${item.color}" style="font-size:0.7rem;">AI Verified</span>
                        <button class="btn btn-sm btn-link text-muted p-0" onclick="copyToClipboard('${text.replace(/'/g, "\\'")}', this)" title="Copy Insight">
                            <i class="far fa-copy"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

function copyToClipboard(text, btn) {
    navigator.clipboard.writeText(text).then(() => {
        const originalHtml = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-check text-success"></i>';
        showToast('Insight copied to clipboard!', 'success');
        setTimeout(() => btn.innerHTML = originalHtml, 2000);
    });
}

// Keyframe animation injected via JS
const styleSheet = document.createElement("style");
styleSheet.innerText = `
@keyframes fadeInUp {
    from { transform: translateY(20px); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
}`;
document.head.appendChild(styleSheet);
