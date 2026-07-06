document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('resume');
    const fileNameDisplay = document.getElementById('file-name');
    const form = document.getElementById('tailor-form');
    const submitBtn = document.getElementById('submit-btn');
    const spinner = document.getElementById('spinner');
    const btnText = submitBtn.querySelector('span');
    const resultsContainer = document.getElementById('results-container');
    
    // File input visual update
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            fileNameDisplay.textContent = e.target.files[0].name;
            fileNameDisplay.style.color = '#60a5fa';
        } else {
            fileNameDisplay.textContent = 'Drag & drop or click to browse';
            fileNameDisplay.style.color = '';
        }
    });

    // Form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // UI Loading state
        submitBtn.disabled = true;
        btnText.textContent = 'Processing...';
        spinner.style.display = 'block';
        resultsContainer.style.display = 'none';

        try {
            const formData = new FormData(form);
            
            const response = await fetch('/api/analyze', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Analysis failed');
            }

            const data = await response.json();
            
            // Populate results
            document.getElementById('ats-score').textContent = `${data.ats_score}%`;
            
            // Set score color based on value
            const scoreEl = document.getElementById('ats-score');
            if (data.ats_score >= 80) scoreEl.style.color = 'var(--success)';
            else if (data.ats_score >= 50) scoreEl.style.color = 'var(--warning)';
            else scoreEl.style.color = 'var(--danger)';

            document.getElementById('matched-count').textContent = data.matched_keywords.length;
            document.getElementById('missing-count').textContent = data.missing_keywords.length;

            // Render keywords
            const renderTags = (containerId, items, cssClass) => {
                const container = document.getElementById(containerId);
                if (items.length === 0) {
                    container.innerHTML = '<span class="tag">None</span>';
                    return;
                }
                container.innerHTML = items.map(item => `<span class="tag ${cssClass}">${item}</span>`).join('');
            };

            renderTags('matched-keywords', data.matched_keywords, 'match');
            renderTags('missing-keywords', data.missing_keywords, 'miss');

            // Render JSON content
            try {
                let contentStr = data.content;
                if (contentStr.startsWith("```")) {
                    contentStr = contentStr.replace(/^```(json)?\s*|\s*```$/g, '').trim();
                }
                const tailoredData = JSON.parse(contentStr);
                
                if (tailoredData.error) {
                    document.getElementById('tailored-output').innerHTML = `<div class="error-msg">${tailoredData.error}</div>`;
                } else {
                    let html = `
                        <div class="json-results">
                            <div class="section-block">
                                <h3><span class="icon">🎯</span> Professional Summary</h3>
                                <p>${tailoredData.tailored_professional_summary || ''}</p>
                            </div>
                            
                            <div class="section-block">
                                <h3><span class="icon">✨</span> Key Skills to Highlight</h3>
                                <div class="keyword-tags highlight-tags">
                                    ${(tailoredData.key_skills_to_highlight || []).map(s => `<span class="tag keyword-tag">${s}</span>`).join('')}
                                </div>
                            </div>
                            
                            <div class="section-block">
                                <h3><span class="icon">📝</span> Recommended Resume Bullets</h3>
                                <ul class="bullet-list">
                                    ${(tailoredData.recommended_resume_bullets || []).map(b => `<li>${b}</li>`).join('')}
                                </ul>
                            </div>
                            
                            <div class="section-block">
                                <h3><span class="icon">💡</span> Experience Improvements</h3>
                                <div class="improvements-grid">
                                    ${(tailoredData.experience_improvements || []).map(exp => `
                                        <div class="improvement-card">
                                            <div class="imp-original"><strong>Original:</strong> ${exp.original}</div>
                                            <div class="imp-rewritten"><strong>Rewritten:</strong> ${exp.rewritten}</div>
                                            <div class="imp-reason"><em>Reason:</em> ${exp.reason}</div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                            
                            <div class="section-block recruiter-feedback">
                                <h3><span class="icon">🔍</span> Recruiter Feedback</h3>
                                <div class="feedback-grid">
                                    <div class="feedback-box strengths">
                                        <h4>Strengths</h4>
                                        <ul>${(tailoredData.recruiter_feedback?.strengths || []).map(s => `<li>${s}</li>`).join('')}</ul>
                                    </div>
                                    <div class="feedback-box weaknesses">
                                        <h4>Weaknesses</h4>
                                        <ul>${(tailoredData.recruiter_feedback?.weaknesses || []).map(s => `<li>${s}</li>`).join('')}</ul>
                                    </div>
                                    <div class="feedback-box top-improvements">
                                        <h4>Top Improvements</h4>
                                        <ul>${(tailoredData.recruiter_feedback?.top_improvements || []).map(s => `<li>${s}</li>`).join('')}</ul>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="section-block">
                                <h3><span class="icon">🚀</span> Final Recommendations</h3>
                                <ul class="recommendation-list">
                                    ${(tailoredData.final_recommendations || []).map(r => `<li>${r}</li>`).join('')}
                                </ul>
                            </div>
                        </div>
                    `;
                    document.getElementById('tailored-output').innerHTML = html;
                }
            } catch (e) {
                console.error("Failed to parse JSON, falling back to markdown", e);
                console.log("Raw content was:", data.content);
                if (typeof marked !== 'undefined') {
                    document.getElementById('tailored-output').innerHTML = marked.parse(data.content);
                } else {
                    document.getElementById('tailored-output').innerHTML = `<pre>${data.content}</pre>`;
                }
            }

            // Show results
            resultsContainer.style.display = 'block';
            resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });

        } catch (error) {
            alert(`Error: ${error.message}`);
            console.error('Error:', error);
        } finally {
            // Reset UI Loading state
            submitBtn.disabled = false;
            btnText.textContent = 'Analyze & Tailor';
            spinner.style.display = 'none';
        }
    });
});
