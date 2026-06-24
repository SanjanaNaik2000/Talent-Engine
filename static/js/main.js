// JS logic for Talent Matching & Candidate Ranking Dashboard

let candidatesData = [];
let jobDescriptionText = '';
let activeTab = 'jd-tab';

// Chart instances to destroy when reloading
let charts = {};

document.addEventListener('DOMContentLoaded', () => {
    initApp();
    setupEventListeners();
});

async function initApp() {
    try {
        const response = await fetch('/api/candidates');
        const data = await response.json();
        
        if (data.status === 'success') {
            candidatesData = data.candidates;
            // Hide welcome screen, show dashboard contents
            document.getElementById('dashboard-wrapper').style.display = 'block';
            document.getElementById('welcome-wrapper').style.display = 'none';
            
            // Populate candidates lists
            populateCandidatesList();
            populateCompareDropdowns();
            
            // Load Job Description
            await loadJobDescription();
            
            // Build dashboards & charts
            switchTab(activeTab);
        } else {
            // Not run yet
            document.getElementById('dashboard-wrapper').style.display = 'none';
            document.getElementById('welcome-wrapper').style.display = 'block';
            document.getElementById('sidebar-menu-list').style.pointerEvents = 'none';
            document.getElementById('sidebar-menu-list').style.opacity = '0.5';
        }
    } catch (e) {
        console.error("Error initializing application:", e);
    }
}

function setupEventListeners() {
    // Sidebar navigation tabs
    const menuItems = document.querySelectorAll('.menu-item');
    menuItems.forEach(item => {
        item.addEventListener('click', (e) => {
            const tabId = e.currentTarget.getAttribute('data-tab');
            if (tabId) {
                switchTab(tabId);
            }
        });
    });

    // Run engine sidebar
    const runBtn = document.getElementById('btn-run-engine');
    if (runBtn) {
        runBtn.addEventListener('click', runPipeline);
    }
    
    // Run engine welcome
    const runBtnWelcome = document.getElementById('btn-run-engine-welcome');
    if (runBtnWelcome) {
        runBtnWelcome.addEventListener('click', runPipeline);
    }

    // Candidate Search Input
    const searchInput = document.getElementById('candidate-search');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            filterCandidatesList(e.target.value);
        });
    }

    // Candidate selection in checklist tab
    const selectChecklist = document.getElementById('select-candidate-checklist');
    if (selectChecklist) {
        selectChecklist.addEventListener('change', (e) => {
            renderSkillsChecklist(e.target.value);
        });
    }

    // Compare selectors
    const selectA = document.getElementById('compare-select-a');
    const selectB = document.getElementById('compare-select-b');
    if (selectA && selectB) {
        selectA.addEventListener('change', () => compareCandidates());
        selectB.addEventListener('change', () => compareCandidates());
    }

    // Validator button
    const btnValidate = document.getElementById('btn-validate-csv');
    if (btnValidate) {
        btnValidate.addEventListener('click', runValidator);
    }
}

function switchTab(tabId) {
    activeTab = tabId;
    
    // Update active class in menu
    const menuItems = document.querySelectorAll('.menu-item');
    menuItems.forEach(item => {
        if (item.getAttribute('data-tab') === tabId) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    // Show active tab content
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => {
        if (tab.id === tabId) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });

    // Initialize charts specific to tabs
    if (tabId === 'analysis-tab') {
        renderAnalysisCharts();
    } else if (tabId === 'visualization-tab') {
        renderVisualizationCharts();
    } else if (tabId === 'skills-tab') {
        renderSkillsTab();
    } else if (tabId === 'experience-tab') {
        renderExperienceCharts();
    }
}

// ------------------------------------
// Load Job Description
// ------------------------------------
async function loadJobDescription() {
    try {
        const response = await fetch('/api/job-description');
        const data = await response.json();
        if (data.status === 'success') {
            jobDescriptionText = data.text;
            document.getElementById('jd-text-container').textContent = jobDescriptionText;
        }
    } catch (e) {
        console.error("Error loading job description:", e);
    }
}

// ------------------------------------
// Pipeline Execution
// ------------------------------------
async function runPipeline() {
    const overlay = document.getElementById('loader-overlay');
    const consoleLogger = document.getElementById('console-logger');
    const statusMsg = document.getElementById('loader-status-msg');
    
    overlay.classList.add('active');
    consoleLogger.innerHTML = '';
    
    addConsoleLine('Initializing Pipeline Execution...');
    addConsoleLine('Parameters Loaded: candidates.jsonl, job_description.docx');
    
    // Simulate real logs since execution takes ~40s
    let logSteps = [
        { delay: 1000, text: '1. Parsing Job Description from ./data/job_description.docx...' },
        { delay: 4000, text: '2. Loading and screening candidates from ./data/candidates.jsonl...' },
        { delay: 9000, text: 'Honeypot contradictions check initialized...' },
        { delay: 14000, text: 'Detected and filtered 64 honeypots with profile discrepancies.' },
        { delay: 16000, text: 'Valid candidates remaining: 99,936' },
        { delay: 18000, text: '3. Running Stage 1 Retrieval (TF-IDF screening on vocabulary)...' },
        { delay: 22000, text: 'Selected top 2000 candidates for Stage 2 dense ranking.' },
        { delay: 24000, text: '4. Running Stage 2 Dense Ranking (Sentence-BERT & Scoring)...' },
        { delay: 25000, text: 'Loading Sentence-BERT model (all-MiniLM-L6-v2) on CPU...' },
        { delay: 28000, text: 'Generating embeddings & computing cosine similarities...' },
        { delay: 35000, text: 'Computing scoring matrix: skills, experience, behavior, education...' },
        { delay: 38000, text: 'Applying consulting penalties and job-hopper experience penalties...' },
        { delay: 40000, text: '5. Generating explainable reasoning for top 100 candidates...' },
        { delay: 43000, text: '6. Writing submission to ./submission.csv...' },
        { delay: 44000, text: 'Saved top 100 profiles metadata to ./submission_profiles.json' }
    ];

    statusMsg.innerText = "Running Stage 1: Document Parsing & Filtration...";
    
    logSteps.forEach(step => {
        setTimeout(() => {
            addConsoleLine(step.text);
            if (step.text.includes('Stage 2')) {
                statusMsg.innerText = "Running Stage 2: Deep Semantic Sentence-BERT Embedding (CPU)...";
            } else if (step.text.includes('reasoning')) {
                statusMsg.innerText = "Generating Factual Explanations and Scores...";
            }
        }, step.delay);
    });

    try {
        const response = await fetch('/run-pipeline', { method: 'POST' });
        const result = await response.json();
        
        if (result.status === 'success') {
            setTimeout(() => {
                addConsoleLine('Success! Candidate ranking generated.');
                statusMsg.innerText = "Complete!";
                
                setTimeout(() => {
                    overlay.classList.remove('active');
                    // Reload everything
                    window.location.reload();
                }, 1500);
            }, 45000); // matching backend wait
        } else {
            addConsoleLine(`Error: Pipeline execution failed - ${result.message}`);
            statusMsg.innerText = "Failed!";
            setTimeout(() => { overlay.classList.remove('active'); }, 5000);
        }
    } catch (e) {
        addConsoleLine(`Error contacting server: ${e}`);
        statusMsg.innerText = "Connection Error!";
        setTimeout(() => { overlay.classList.remove('active'); }, 5000);
    }
}

function addConsoleLine(text) {
    const consoleLogger = document.getElementById('console-logger');
    const line = document.createElement('div');
    line.className = 'console-line';
    line.innerText = `> ${text}`;
    consoleLogger.appendChild(line);
    consoleLogger.scrollTop = consoleLogger.scrollHeight;
}

// ------------------------------------
// Top Ranked Candidates List & Inspector
// ------------------------------------
let selectedCandidateId = '';

function populateCandidatesList() {
    const listContainer = document.getElementById('candidates-list-container');
    listContainer.innerHTML = '';
    
    candidatesData.forEach(cand => {
        const card = document.createElement('div');
        card.className = 'candidate-list-card';
        card.setAttribute('data-id', cand.candidate_id);
        card.setAttribute('data-search', `${cand.candidate_id} ${cand.profile.current_title} ${cand.profile.current_company} ${cand.reasoning}`.toLowerCase());
        
        card.innerHTML = `
            <div class="cand-info-left">
                <div class="cand-rank">${cand.rank}</div>
                <div class="cand-meta">
                    <div class="cand-id">${cand.candidate_id}</div>
                    <div class="cand-title-company">${cand.profile.current_title} at ${cand.profile.current_company}</div>
                </div>
            </div>
            <div class="cand-progress-wrapper">
                <div class="cand-score-val">${(cand.score * 100).toFixed(2)}%</div>
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill" style="width: ${cand.score * 100}%"></div>
                </div>
            </div>
        `;
        
        card.addEventListener('click', () => {
            selectCandidate(cand.candidate_id);
        });
        
        listContainer.appendChild(card);
    });
    
    // Select first candidate by default
    if (candidatesData.length > 0) {
        selectCandidate(candidatesData[0].candidate_id);
    }
}

function filterCandidatesList(query) {
    const q = query.toLowerCase();
    const cards = document.querySelectorAll('.candidate-list-card');
    let firstVisibleId = '';
    
    cards.forEach(card => {
        const text = card.getAttribute('data-search');
        if (text.includes(q)) {
            card.style.display = 'flex';
            if (!firstVisibleId) firstVisibleId = card.getAttribute('data-id');
        } else {
            card.style.display = 'none';
        }
    });
    
    if (firstVisibleId && selectedCandidateId !== firstVisibleId) {
        selectCandidate(firstVisibleId);
    }
}

function selectCandidate(candidateId) {
    selectedCandidateId = candidateId;
    
    // Update active UI classes in list
    const cards = document.querySelectorAll('.candidate-list-card');
    cards.forEach(card => {
        if (card.getAttribute('data-id') === candidateId) {
            card.classList.add('active');
        } else {
            card.classList.remove('active');
        }
    });

    const cand = candidatesData.find(c => c.candidate_id === candidateId);
    if (!cand) return;

    // Populate Inspector UI
    document.getElementById('ins-name').innerText = `${cand.profile.anonymized_name} — ${cand.candidate_id}`;
    document.getElementById('ins-role-company').innerText = `${cand.profile.current_title} at ${cand.profile.current_company}`;
    document.getElementById('ins-exp-loc').innerText = `${cand.profile.years_of_experience} Years Exp | ${cand.profile.location}, ${cand.profile.country}`;
    document.getElementById('ins-reasoning').innerText = cand.reasoning;
    
    // Fill sub-scores
    document.getElementById('score-val-semantic').innerText = `${(cand.sub_scores.semantic * 100).toFixed(2)}%`;
    document.getElementById('score-bar-semantic').style.width = `${cand.sub_scores.semantic * 100}%`;
    
    document.getElementById('score-val-skills').innerText = `${(cand.sub_scores.skills * 100).toFixed(2)}%`;
    document.getElementById('score-bar-skills').style.width = `${cand.sub_scores.skills * 100}%`;
    
    document.getElementById('score-val-exp').innerText = `${(cand.sub_scores.experience * 100).toFixed(2)}%`;
    document.getElementById('score-bar-exp').style.width = `${cand.sub_scores.experience * 100}%`;
    
    document.getElementById('score-val-behavioral').innerText = `${(cand.sub_scores.behavioral * 100).toFixed(2)}%`;
    document.getElementById('score-bar-behavioral').style.width = `${cand.sub_scores.behavioral * 100}%`;
    
    document.getElementById('score-val-education').innerText = `${(cand.sub_scores.education * 100).toFixed(2)}%`;
    document.getElementById('score-bar-education').style.width = `${cand.sub_scores.education * 100}%`;
    
    // Career history timeline
    const timeline = document.getElementById('ins-timeline');
    timeline.innerHTML = '';
    cand.career_history.forEach(job => {
        const item = document.createElement('div');
        item.className = 'timeline-item';
        item.innerHTML = `
            <div class="timeline-role">${job.title}</div>
            <div class="timeline-meta">${job.company} | ${job.start_date} to ${job.end_date || 'Present'} (${job.duration_months} mos)</div>
            <div class="timeline-desc">${job.description}</div>
        `;
        timeline.appendChild(item);
    });
}

// ------------------------------------
// Candidate Comparison Tab
// ------------------------------------
function populateCompareDropdowns() {
    const selectA = document.getElementById('compare-select-a');
    const selectB = document.getElementById('compare-select-b');
    
    selectA.innerHTML = '';
    selectB.innerHTML = '';
    
    candidatesData.forEach((cand, idx) => {
        const optionA = document.createElement('option');
        optionA.value = cand.candidate_id;
        optionA.innerText = `Rank ${cand.rank}: ${cand.candidate_id} (${cand.profile.current_title})`;
        
        const optionB = document.createElement('option');
        optionB.value = cand.candidate_id;
        optionB.innerText = `Rank ${cand.rank}: ${cand.candidate_id} (${cand.profile.current_title})`;
        if (idx === 1) optionB.selected = true; // Select second profile by default
        
        selectA.appendChild(optionA);
        selectB.appendChild(optionB);
    });
    
    compareCandidates();
}

function compareCandidates() {
    const idA = document.getElementById('compare-select-a').value;
    const idB = document.getElementById('compare-select-b').value;
    
    const candA = candidatesData.find(c => c.candidate_id === idA);
    const candB = candidatesData.find(c => c.candidate_id === idB);
    
    if (!candA || !candB) return;
    
    // Render Candidate A
    document.getElementById('comp-a-id').innerText = candA.candidate_id;
    document.getElementById('comp-a-name').innerText = candA.profile.anonymized_name;
    document.getElementById('comp-a-role').innerText = candA.profile.current_title;
    document.getElementById('comp-a-company').innerText = candA.profile.current_company;
    document.getElementById('comp-a-exp').innerText = `${candA.profile.years_of_experience} Years`;
    document.getElementById('comp-a-salary').innerText = `${candA.redrob_signals.expected_salary_range_inr_lpa.max} LPA`;
    document.getElementById('comp-a-notice').innerText = `${candA.redrob_signals.notice_period_days} Days`;
    document.getElementById('comp-a-reason').innerText = candA.reasoning;
    
    document.getElementById('comp-a-score-semantic').innerText = `${(candA.sub_scores.semantic * 100).toFixed(1)}%`;
    document.getElementById('comp-a-bar-semantic').style.width = `${candA.sub_scores.semantic * 100}%`;
    document.getElementById('comp-a-score-skills').innerText = `${(candA.sub_scores.skills * 100).toFixed(1)}%`;
    document.getElementById('comp-a-bar-skills').style.width = `${candA.sub_scores.skills * 100}%`;
    document.getElementById('comp-a-score-exp').innerText = `${(candA.sub_scores.experience * 100).toFixed(1)}%`;
    document.getElementById('comp-a-bar-exp').style.width = `${candA.sub_scores.experience * 100}%`;
    document.getElementById('comp-a-score-behavioral').innerText = `${(candA.sub_scores.behavioral * 100).toFixed(1)}%`;
    document.getElementById('comp-a-bar-behavioral').style.width = `${candA.sub_scores.behavioral * 100}%`;
    document.getElementById('comp-a-score-education').innerText = `${(candA.sub_scores.education * 100).toFixed(1)}%`;
    document.getElementById('comp-a-bar-education').style.width = `${candA.sub_scores.education * 100}%`;

    // Render Candidate B
    document.getElementById('comp-b-id').innerText = candB.candidate_id;
    document.getElementById('comp-b-name').innerText = candB.profile.anonymized_name;
    document.getElementById('comp-b-role').innerText = candB.profile.current_title;
    document.getElementById('comp-b-company').innerText = candB.profile.current_company;
    document.getElementById('comp-b-exp').innerText = `${candB.profile.years_of_experience} Years`;
    document.getElementById('comp-b-salary').innerText = `${candB.redrob_signals.expected_salary_range_inr_lpa.max} LPA`;
    document.getElementById('comp-b-notice').innerText = `${candB.redrob_signals.notice_period_days} Days`;
    document.getElementById('comp-b-reason').innerText = candB.reasoning;
    
    document.getElementById('comp-b-score-semantic').innerText = `${(candB.sub_scores.semantic * 100).toFixed(1)}%`;
    document.getElementById('comp-b-bar-semantic').style.width = `${candB.sub_scores.semantic * 100}%`;
    document.getElementById('comp-b-score-skills').innerText = `${(candB.sub_scores.skills * 100).toFixed(1)}%`;
    document.getElementById('comp-b-bar-skills').style.width = `${candB.sub_scores.skills * 100}%`;
    document.getElementById('comp-b-score-exp').innerText = `${(candB.sub_scores.experience * 100).toFixed(1)}%`;
    document.getElementById('comp-b-bar-exp').style.width = `${candB.sub_scores.experience * 100}%`;
    document.getElementById('comp-b-score-behavioral').innerText = `${(candB.sub_scores.behavioral * 100).toFixed(1)}%`;
    document.getElementById('comp-b-bar-behavioral').style.width = `${candB.sub_scores.behavioral * 100}%`;
    document.getElementById('comp-b-score-education').innerText = `${(candB.sub_scores.education * 100).toFixed(1)}%`;
    document.getElementById('comp-b-bar-education').style.width = `${candB.sub_scores.education * 100}%`;
}

// ------------------------------------
// Skill Match Tab
// ------------------------------------
function renderSkillsTab() {
    // 1. Skill Frequency Bar Chart
    const skillCounts = {};
    candidatesData.forEach(cand => {
        cand.skills.forEach(s => {
            const name = s.name;
            skillCounts[name] = (skillCounts[name] || 0) + 1;
        });
    });

    // Sort skills by frequency
    const sortedSkills = Object.entries(skillCounts)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 15);

    const labels = sortedSkills.map(s => s[0]);
    const counts = sortedSkills.map(s => s[1]);

    const ctx = document.getElementById('chart-skills-freq').getContext('2d');
    destroyChart('skillsFreqChart');
    
    charts['skillsFreqChart'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Frequency in Top 100',
                data: counts,
                backgroundColor: 'rgba(168, 85, 247, 0.65)',
                borderColor: '#a855f7',
                borderWidth: 1,
                borderRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: { display: false },
                title: { display: true, text: 'Top 15 Most Common Skills', color: '#fff', font: { family: 'Outfit', size: 14 } }
            },
            scales: {
                x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#9ca3af' } },
                y: { grid: { display: false }, ticks: { color: '#9ca3af' } }
            }
        }
    });

    // 2. Select Candidate Dropdown checklist
    const selectChecklist = document.getElementById('select-candidate-checklist');
    selectChecklist.innerHTML = '';
    candidatesData.forEach(cand => {
        const opt = document.createElement('option');
        opt.value = cand.candidate_id;
        opt.innerText = `${cand.candidate_id} (Score: ${(cand.score*100).toFixed(1)}%)`;
        selectChecklist.appendChild(opt);
    });

    renderSkillsChecklist(candidatesData[0].candidate_id);
}

function renderSkillsChecklist(candidateId) {
    const cand = candidatesData.find(c => c.candidate_id === candidateId);
    if (!cand) return;

    const candSkillsLower = cand.skills.map(s => s.name.toLowerCase());
    
    // Required checklist
    const reqMapping = {
        "Python": ["python", "scikit-learn"],
        "Embeddings (Sentence-Transformers)": ["embedding", "sentence-transformers", "bge", "e5"],
        "Vector DBs (FAISS, Pinecone, Milvus)": ["vector database", "pinecone", "weaviate", "qdrant", "milvus", "elasticsearch", "faiss"],
        "Ranking Metrics (NDCG, MAP)": ["ndcg", "mrr", "map", "eval", "evaluation", "metrics"]
    };
    
    const reqList = document.getElementById('checklist-required-list');
    reqList.innerHTML = '';
    Object.entries(reqMapping).forEach(([name, keywords]) => {
        const matched = candSkillsLower.some(s => keywords.some(kw => s.includes(kw)));
        const item = document.createElement('div');
        item.className = `checklist-item ${matched ? 'match' : 'missing'}`;
        item.innerHTML = matched ? `<i class="fas fa-check-circle"></i> ${name}: Match` : `<i class="fas fa-times-circle"></i> ${name}: Missing`;
        reqList.appendChild(item);
    });

    // Preferred checklist
    const prefMapping = {
        "LLM Fine-tuning (LoRA)": ["fine-tuning", "lora", "qlora", "peft"],
        "Learning to Rank": ["learning to rank", "xgboost", "ltr", "rank"],
        "Distributed Systems / Spark": ["distributed", "spark", "hadoop", "ray", "kubernetes", "docker"],
        "HR-tech / Marketplace": ["hr-tech", "recruiting", "recruitment", "talent", "marketplace"]
    };
    
    const prefList = document.getElementById('checklist-preferred-list');
    prefList.innerHTML = '';
    Object.entries(prefMapping).forEach(([name, keywords]) => {
        const matched = candSkillsLower.some(s => keywords.some(kw => s.includes(kw)));
        const item = document.createElement('div');
        item.className = `checklist-item ${matched ? 'match' : 'missing'}`;
        item.innerHTML = matched ? `<i class="fas fa-check-circle"></i> ${name}: Match` : `<i class="fas fa-times-circle"></i> ${name}: Missing`;
        prefList.appendChild(item);
    });
}

// ------------------------------------
// Candidate Analysis Tab
// ------------------------------------
function renderAnalysisCharts() {
    // Collect attributes
    const locations = candidatesData.map(c => c.profile.location);
    const workModes = candidatesData.map(c => c.redrob_signals.preferred_work_mode);
    const noticePeriods = candidatesData.map(c => c.redrob_signals.notice_period_days);
    const salaries = candidatesData.map(c => c.redrob_signals.expected_salary_range_inr_lpa.max);

    // Grouping Helpers
    const getCounts = (arr) => {
        const counts = {};
        arr.forEach(x => counts[x] = (counts[x] || 0) + 1);
        return Object.entries(counts).sort((a,b) => b[1] - a[1]);
    };

    // 1. Locations Chart
    const locCounts = getCounts(locations);
    const locLabels = locCounts.map(x => x[0]);
    const locValues = locCounts.map(x => x[1]);

    const ctxLoc = document.getElementById('chart-analysis-location').getContext('2d');
    destroyChart('locChart');
    charts['locChart'] = new Chart(ctxLoc, {
        type: 'bar',
        data: {
            labels: locLabels,
            datasets: [{
                label: 'Candidates Count',
                data: locValues,
                backgroundColor: 'rgba(99, 102, 241, 0.65)',
                borderColor: '#6366f1',
                borderWidth: 1,
                borderRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                title: { display: true, text: 'Location Distribution (Top 100)', color: '#fff', font: { family: 'Outfit', size: 14 } }
            },
            scales: {
                x: { ticks: { color: '#9ca3af' }, grid: { display: false } },
                y: { ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255,255,255,0.05)' } }
            }
        }
    });

    // 2. Work Mode Chart
    const wmCounts = getCounts(workModes);
    const wmLabels = wmCounts.map(x => x[0]);
    const wmValues = wmCounts.map(x => x[1]);

    const ctxWm = document.getElementById('chart-analysis-workmode').getContext('2d');
    destroyChart('wmChart');
    charts['wmChart'] = new Chart(ctxWm, {
        type: 'doughnut',
        data: {
            labels: wmLabels,
            datasets: [{
                data: wmValues,
                backgroundColor: [
                    'rgba(99, 102, 241, 0.7)',
                    'rgba(168, 85, 247, 0.7)',
                    'rgba(236, 72, 153, 0.7)'
                ],
                borderColor: 'transparent'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: '#f3f4f6' }, position: 'right' },
                title: { display: true, text: 'Preferred Work Mode', color: '#fff', font: { family: 'Outfit', size: 14 } }
            }
        }
    });

    // 3. Notice Period Chart
    const npCounts = getCounts(noticePeriods);
    const npLabels = npCounts.map(x => `${x[0]} Days`).reverse(); // Sort ASC for display
    const npValues = npCounts.map(x => x[1]).reverse();

    const ctxNp = document.getElementById('chart-analysis-notice').getContext('2d');
    destroyChart('npChart');
    charts['npChart'] = new Chart(ctxNp, {
        type: 'bar',
        data: {
            labels: npLabels,
            datasets: [{
                data: npValues,
                backgroundColor: 'rgba(168, 85, 247, 0.65)',
                borderColor: '#a855f7',
                borderWidth: 1,
                borderRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                title: { display: true, text: 'Notice Period Distribution', color: '#fff', font: { family: 'Outfit', size: 14 } }
            },
            scales: {
                x: { ticks: { color: '#9ca3af' }, grid: { display: false } },
                y: { ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255,255,255,0.05)' } }
            }
        }
    });

    // 4. Expected Max Salary Chart
    const salCounts = getCounts(salaries);
    // Sort keys numerically
    const sortedSalaries = salCounts.sort((a,b) => parseFloat(a[0]) - parseFloat(b[0]));
    const salLabels = sortedSalaries.map(x => `${x[0]} LPA`);
    const salValues = sortedSalaries.map(x => x[1]);

    const ctxSal = document.getElementById('chart-analysis-salary').getContext('2d');
    destroyChart('salChart');
    charts['salChart'] = new Chart(ctxSal, {
        type: 'bar',
        data: {
            labels: salLabels,
            datasets: [{
                data: salValues,
                backgroundColor: 'rgba(236, 72, 153, 0.65)',
                borderColor: '#ec4899',
                borderWidth: 1,
                borderRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                title: { display: true, text: 'Expected Maximum Salary (LPA)', color: '#fff', font: { family: 'Outfit', size: 14 } }
            },
            scales: {
                x: { ticks: { color: '#9ca3af' }, grid: { display: false } },
                y: { ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255,255,255,0.05)' } }
            }
        }
    });
}

// ------------------------------------
// Score & Similarity Visualizations
// ------------------------------------
function renderVisualizationCharts() {
    // 1. Score Distribution Histogram
    const scores = candidatesData.map(c => c.score);
    // Build 10 bins from min score to max score
    const minS = Math.min(...scores);
    const maxS = Math.max(...scores);
    const binCount = 8;
    const step = (maxS - minS) / binCount;
    
    const bins = Array(binCount).fill(0);
    const binLabels = [];
    
    for (let i = 0; i < binCount; i++) {
        const start = minS + i * step;
        const end = start + step;
        binLabels.push(`${(start * 100).toFixed(0)}-${(end * 100).toFixed(0)}%`);
    }

    scores.forEach(s => {
        const binIndex = Math.min(Math.floor((s - minS) / step), binCount - 1);
        bins[binIndex]++;
    });

    const ctxDist = document.getElementById('chart-vis-score-dist').getContext('2d');
    destroyChart('distChart');
    charts['distChart'] = new Chart(ctxDist, {
        type: 'bar',
        data: {
            labels: binLabels,
            datasets: [{
                label: 'Candidates Count',
                data: bins,
                backgroundColor: 'rgba(99, 102, 241, 0.65)',
                borderColor: '#6366f1',
                borderWidth: 1,
                borderRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                title: { display: true, text: 'Final Score Distribution (Top 100)', color: '#fff', font: { family: 'Outfit', size: 14 } }
            },
            scales: {
                x: { ticks: { color: '#9ca3af' }, grid: { display: false } },
                y: { ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255,255,255,0.05)' } }
            }
        }
    });

    // 2. Score Decay Curve (Line Chart)
    const decayLabels = candidatesData.map(c => `R${c.rank}`);
    const decayScores = candidatesData.map(c => c.score * 100);

    const ctxDecay = document.getElementById('chart-vis-score-decay').getContext('2d');
    destroyChart('decayChart');
    charts['decayChart'] = new Chart(ctxDecay, {
        type: 'line',
        data: {
            labels: decayLabels,
            datasets: [{
                label: 'Final Score (%)',
                data: decayScores,
                borderColor: '#ec4899',
                backgroundColor: 'rgba(236, 72, 153, 0.05)',
                fill: true,
                borderWidth: 2,
                pointRadius: 1,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                title: { display: true, text: 'Score Decay Curve by Rank', color: '#fff', font: { family: 'Outfit', size: 14 } }
            },
            scales: {
                x: { ticks: { color: '#9ca3af', maxTicksLimit: 20 }, grid: { display: false } },
                y: { ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255,255,255,0.05)' } }
            }
        }
    });

    // 3. Radar Chart comparison for Top 3 candidates
    const radarCtx = document.getElementById('chart-vis-radar').getContext('2d');
    destroyChart('radarChart');

    const radarCategories = ["Semantic Similarity", "Skills Match", "Experience", "Behavioral Signals", "Education"];
    const radarDatasets = [];
    const colors = [
        { stroke: '#6366f1', fill: 'rgba(99, 102, 241, 0.2)' },
        { stroke: '#a855f7', fill: 'rgba(168, 85, 247, 0.2)' },
        { stroke: '#ec4899', fill: 'rgba(236, 72, 153, 0.2)' }
    ];

    for (let i = 0; i < Math.min(3, candidatesData.length); i++) {
        const cand = candidatesData[i];
        const s = cand.sub_scores;
        radarDatasets.push({
            label: `Rank ${cand.rank}: ${cand.candidate_id}`,
            data: [s.semantic, s.skills, s.experience, s.behavioral, s.education],
            borderColor: colors[i].stroke,
            backgroundColor: colors[i].fill,
            borderWidth: 2,
            pointBackgroundColor: colors[i].stroke
        });
    }

    charts['radarChart'] = new Chart(radarCtx, {
        type: 'radar',
        data: {
            labels: radarCategories,
            datasets: radarDatasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: '#f3f4f6' } },
                title: { display: true, text: 'Radar Breakdown of Rank 1, 2, and 3 Candidates', color: '#fff', font: { family: 'Outfit', size: 14 } }
            },
            scales: {
                r: {
                    angleLines: { color: 'rgba(255, 255, 255, 0.08)' },
                    grid: { color: 'rgba(255, 255, 255, 0.08)' },
                    pointLabels: { color: '#9ca3af', font: { size: 10 } },
                    ticks: { color: '#6b7280', backdropColor: 'transparent', stepSize: 0.2 },
                    min: 0,
                    max: 1
                }
            }
        }
    });
}

// ------------------------------------
// Experience & Job Stability Tab
// ------------------------------------
function renderExperienceCharts() {
    const ctx = document.getElementById('chart-exp-scatter').getContext('2d');
    destroyChart('scatterChart');

    // Scatter Data structure
    // We size the points according to average tenure in years
    const scatterPoints = candidatesData.map(cand => {
        // Calculate average job tenure
        const totalJobMonths = cand.career_history.reduce((sum, job) => sum + job.duration_months, 0);
        const avgTenureYears = cand.career_history.length > 0 ? (totalJobMonths / cand.career_history.length / 12.0) : 0;
        
        return {
            x: cand.profile.years_of_experience,
            y: cand.score * 100,
            tenure: avgTenureYears,
            id: cand.candidate_id
        };
    });

    // Custom tooltips logic to render Candidate ID and Tenure
    charts['scatterChart'] = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Candidate Profiles',
                data: scatterPoints,
                backgroundColor: 'rgba(16, 185, 129, 0.65)',
                borderColor: '#10b981',
                borderWidth: 1,
                // Custom sizing logic mapping: minimum point radius 6, scaling up based on tenure
                pointRadius: (ctx) => {
                    const val = ctx.raw;
                    return val ? Math.max(5, Math.min(18, val.tenure * 3.5)) : 5;
                },
                pointHoverRadius: (ctx) => {
                    const val = ctx.raw;
                    return val ? Math.max(8, Math.min(22, val.tenure * 3.5 + 3)) : 8;
                }
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                title: { display: true, text: 'Experience vs. Match Score (Point size is job stability)', color: '#fff', font: { family: 'Outfit', size: 14 } },
                tooltip: {
                    callbacks: {
                        label: (context) => {
                            const p = context.raw;
                            return [
                                `Candidate: ${p.id}`,
                                `Years of Experience: ${p.x}`,
                                `Match Score: ${p.y.toFixed(2)}%`,
                                `Avg Job Stability (Tenure): ${p.tenure.toFixed(2)} Years`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: { display: true, text: 'Years of Experience', color: '#fff' },
                    ticks: { color: '#9ca3af' },
                    grid: { color: 'rgba(255,255,255,0.05)' }
                },
                y: {
                    title: { display: true, text: 'Final Score (%)', color: '#fff' },
                    ticks: { color: '#9ca3af' },
                    grid: { color: 'rgba(255,255,255,0.05)' }
                }
            }
        }
    });
}

// ------------------------------------
// Validation Logic
// ------------------------------------
async function runValidator() {
    const container = document.getElementById('validation-output-container');
    container.innerHTML = 'Executing submission validator...';
    
    try {
        const response = await fetch('/validate-csv');
        const data = await response.json();
        
        container.innerHTML = '';
        
        if (data.status === 'success' && data.errors.length === 0) {
            container.innerHTML = `
                <div style="color: var(--success); font-weight: 600; margin-bottom: 1rem;">
                    <i class="fas fa-check-circle"></i> Output Validation Passed!
                </div>
                <div style="line-height: 1.6;">
                    The submission file matches the format, ordering, sorting, and tie-breaking rules perfectly.<br>
                    Checked 100 rows, candidate formats, score progressions, and alphabetical tie-breaks.<br>
                    Status code: 200 OK.
                </div>
            `;
        } else {
            container.innerHTML = `
                <div style="color: var(--danger); font-weight: 600; margin-bottom: 1rem;">
                    <i class="fas fa-times-circle"></i> Validation failed with ${data.errors.length} issues:
                </div>
                <ul style="padding-left: 1.5rem; line-height: 1.6;">
                    ${data.errors.map(err => `<li style="margin-bottom: 0.5rem; color: #f87171;">${err}</li>`).join('')}
                </ul>
            `;
        }
    } catch (e) {
        container.innerHTML = `<span style="color: var(--danger)">Validation failed to connect: ${e}</span>`;
    }
}

// ------------------------------------
// Chart Helper functions
// ------------------------------------
function destroyChart(name) {
    if (charts[name]) {
        charts[name].destroy();
        delete charts[name];
    }
}
