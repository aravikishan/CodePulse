/* ====================================================================
   CodePulse -- Client-side logic
   CodeMirror integration, Chart.js rendering, API calls
   ==================================================================== */

let editor = null;

const GRADE_COLORS = {
    A: "#3fb950",
    B: "#58a6ff",
    C: "#d29922",
    D: "#db6d28",
    F: "#f85149",
};

/* ── CodeMirror initialization ─────────────────────────────────────── */

function initCodeEditor() {
    const textarea = document.getElementById("code-input");
    if (!textarea) return;

    // Only initialize if CodeMirror is available
    if (typeof CodeMirror === "undefined") return;

    editor = CodeMirror.fromTextArea(textarea, {
        mode: "python",
        theme: "dracula",
        lineNumbers: true,
        indentUnit: 4,
        tabSize: 4,
        indentWithTabs: false,
        lineWrapping: false,
        matchBrackets: true,
        autoCloseBrackets: true,
        styleActiveLine: true,
        viewportMargin: Infinity,
        extraKeys: {
            "Ctrl-Enter": function() { analyzeCode(); },
            "Cmd-Enter": function() { analyzeCode(); },
            "Tab": function(cm) {
                if (cm.somethingSelected()) {
                    cm.indentSelection("add");
                } else {
                    cm.replaceSelection("    ", "end");
                }
            },
        },
    });

    editor.setSize(null, 340);
}

function getCode() {
    if (editor) {
        return editor.getValue();
    }
    const textarea = document.getElementById("code-input");
    return textarea ? textarea.value : "";
}

function setCode(code) {
    if (editor) {
        editor.setValue(code);
    } else {
        const textarea = document.getElementById("code-input");
        if (textarea) textarea.value = code;
    }
}

/* ── Analyze code ──────────────────────────────────────────────────── */

async function analyzeCode() {
    const code = getCode().trim();
    if (!code) {
        showNotification("Please enter some Python code to analyze.", "warning");
        return;
    }

    const filenameInput = document.getElementById("filename");
    const filename = filenameInput ? filenameInput.value.trim() || "untitled.py" : "untitled.py";

    const loading = document.getElementById("loading");
    const results = document.getElementById("results-panel");

    if (loading) loading.style.display = "block";
    if (results) results.style.display = "none";

    try {
        const response = await fetch("/api/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ code, filename }),
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({ error: "Analysis failed" }));
            throw new Error(err.error || "Analysis failed");
        }

        const data = await response.json();
        renderResults(data);
    } catch (error) {
        showNotification("Error: " + error.message, "error");
    } finally {
        if (loading) loading.style.display = "none";
    }
}

/* ── Render results ────────────────────────────────────────────────── */

function renderResults(data) {
    const panel = document.getElementById("results-panel");
    if (!panel) return;
    panel.style.display = "block";

    // Grade badge
    const badge = document.getElementById("grade-badge");
    if (badge) {
        badge.textContent = data.grade;
        badge.className = "grade-badge grade-lg grade-" + data.grade.toLowerCase();
    }

    // Stats
    setText("stat-lines", data.total_lines);
    setText("stat-code-lines", data.code_lines || 0);
    setText("stat-functions", data.functions_count);
    setText("stat-classes", data.classes_count);
    setText("stat-complexity", data.complexity_score);
    setText("stat-mi", data.maintainability_index ? data.maintainability_index.toFixed(1) : "0");

    // Halstead metrics
    const halsteadEl = document.getElementById("halstead-metrics");
    if (halsteadEl) {
        halsteadEl.innerHTML = [
            metricRow("Volume", data.halstead_volume || 0),
            metricRow("Difficulty", data.halstead_difficulty || 0),
            metricRow("Effort", data.halstead_effort || 0),
            metricRow("Est. Bugs", data.halstead_bugs || 0),
            metricRow("Est. Time (s)", data.halstead_time || 0),
        ].join("");
    }

    // Complexity chart
    renderComplexityChart(data.functions || []);

    // Smells
    const smellCount = document.getElementById("smell-count");
    if (smellCount) smellCount.textContent = data.smell_count;

    const smellsList = document.getElementById("smells-list");
    if (smellsList) {
        if (data.smells && data.smells.length > 0) {
            smellsList.innerHTML = data.smells.map(s => `
                <div class="smell-item">
                    <span class="severity-badge severity-${s.severity || "info"}">${s.severity || "info"}</span>
                    <span class="smell-type-tag">${escapeHtml(s.type || "")}</span>
                    <span class="smell-message">${escapeHtml(s.message)}</span>
                    ${s.line ? `<span class="smell-line">Line ${s.line}</span>` : ""}
                </div>
            `).join("");
        } else {
            smellsList.innerHTML = '<p class="empty-state">No code smells detected. Nice work!</p>';
        }
    }

    // Functions table
    const funcBody = document.getElementById("functions-tbody");
    if (funcBody) {
        if (data.functions && data.functions.length > 0) {
            funcBody.innerHTML = data.functions.map(fn => `
                <tr>
                    <td><code>${escapeHtml(fn.name)}</code></td>
                    <td>${fn.line}</td>
                    <td>${fn.arg_count}</td>
                    <td><span class="complexity-val ${fn.complexity > 10 ? 'text-red' : fn.complexity > 5 ? 'text-yellow' : 'text-green'}">${fn.complexity}</span></td>
                    <td>${fn.nesting_depth || 0}</td>
                    <td>${fn.lines || "N/A"}</td>
                </tr>
            `).join("");
        } else {
            funcBody.innerHTML = '<tr><td colspan="6" class="empty-state">No functions found.</td></tr>';
        }
    }

    // Classes table
    const classBody = document.getElementById("classes-tbody");
    if (classBody) {
        if (data.classes && data.classes.length > 0) {
            classBody.innerHTML = data.classes.map(cls => `
                <tr>
                    <td><code>${escapeHtml(cls.name)}</code></td>
                    <td>${cls.line}</td>
                    <td>${cls.method_count || 0}</td>
                    <td>${(cls.bases || []).join(", ") || "None"}</td>
                    <td>${cls.lines || "N/A"}</td>
                </tr>
            `).join("");
        } else {
            classBody.innerHTML = '<tr><td colspan="5" class="empty-state">No classes found.</td></tr>';
        }
    }

    // Scroll to results
    panel.scrollIntoView({ behavior: "smooth", block: "start" });
}

/* ── Load sample code ──────────────────────────────────────────────── */

async function loadSampleCode() {
    try {
        const response = await fetch("/api/sample");
        if (response.ok) {
            const data = await response.json();
            setCode(data.code);
            const filenameInput = document.getElementById("filename");
            if (filenameInput) filenameInput.value = data.filename || "sample.py";
            showNotification("Sample code loaded!", "success");
        } else {
            setCode(getFallbackSample());
        }
    } catch (e) {
        setCode(getFallbackSample());
    }
}

function getFallbackSample() {
    return `import os
from collections import defaultdict


class DataProcessor:
    """Process and aggregate data records."""

    def __init__(self, source_path, delimiter=","):
        self.source_path = source_path
        self.delimiter = delimiter
        self.records = []

    def load(self):
        """Load records from the source file."""
        if not os.path.exists(self.source_path):
            raise FileNotFoundError(f"Not found: {self.source_path}")
        with open(self.source_path) as fh:
            for line in fh:
                parts = line.strip().split(self.delimiter)
                if len(parts) >= 2:
                    self.records.append({"key": parts[0], "value": parts[1]})

    def aggregate(self, group_field="key"):
        """Group records by field."""
        groups = defaultdict(list)
        for record in self.records:
            if group_field in record:
                groups[record[group_field]].append(record)
        return dict(groups)
`;
}

/* ── Chart rendering ───────────────────────────────────────────────── */

let complexityChartInstance = null;
let gradeChartInstance = null;
let metricsChartInstance = null;

function renderComplexityChart(functions) {
    const canvas = document.getElementById("complexityChart");
    if (!canvas || typeof Chart === "undefined") return;

    if (complexityChartInstance) {
        complexityChartInstance.destroy();
    }

    if (!functions || functions.length === 0) {
        canvas.parentElement.innerHTML += '<p class="empty-state">No functions to chart.</p>';
        return;
    }

    const labels = functions.map(f => f.name);
    const complexities = functions.map(f => f.complexity);
    const colors = complexities.map(c =>
        c > 10 ? GRADE_COLORS.F : c > 5 ? GRADE_COLORS.C : GRADE_COLORS.A
    );

    complexityChartInstance = new Chart(canvas, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Cyclomatic Complexity",
                data: complexities,
                backgroundColor: colors,
                borderColor: colors,
                borderWidth: 1,
                borderRadius: 4,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { color: "#8b949e", stepSize: 1 },
                    grid: { color: "rgba(48, 54, 61, 0.5)" },
                },
                x: {
                    ticks: { color: "#8b949e", maxRotation: 45 },
                    grid: { display: false },
                },
            },
        },
    });
}

function renderGradeChart(gradeData) {
    const canvas = document.getElementById("gradeChart");
    if (!canvas || typeof Chart === "undefined") return;

    if (gradeChartInstance) gradeChartInstance.destroy();

    const grades = ["A", "B", "C", "D", "F"];
    const counts = grades.map(g => gradeData[g] || 0);
    const colors = grades.map(g => GRADE_COLORS[g]);

    gradeChartInstance = new Chart(canvas, {
        type: "doughnut",
        data: {
            labels: grades,
            datasets: [{
                data: counts,
                backgroundColor: colors,
                borderColor: "#161b22",
                borderWidth: 2,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: "bottom",
                    labels: { color: "#c9d1d9", padding: 12, font: { size: 12 } },
                },
            },
        },
    });
}

function renderMetricsChart(avgComplexity, avgMI, avgSmells) {
    const canvas = document.getElementById("metricsChart");
    if (!canvas || typeof Chart === "undefined") return;

    if (metricsChartInstance) metricsChartInstance.destroy();

    metricsChartInstance = new Chart(canvas, {
        type: "radar",
        data: {
            labels: ["Complexity", "Maintainability", "Smells"],
            datasets: [{
                label: "Averages",
                data: [
                    Math.min(avgComplexity, 50),
                    avgMI,
                    Math.min(avgSmells * 10, 100),
                ],
                backgroundColor: "rgba(88, 166, 255, 0.2)",
                borderColor: "#58a6ff",
                pointBackgroundColor: "#58a6ff",
                pointBorderColor: "#fff",
                borderWidth: 2,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100,
                    ticks: { color: "#8b949e", backdropColor: "transparent" },
                    grid: { color: "rgba(48, 54, 61, 0.5)" },
                    pointLabels: { color: "#c9d1d9", font: { size: 11 } },
                },
            },
            plugins: {
                legend: { display: false },
            },
        },
    });
}

/* ── Navigation toggle ─────────────────────────────────────────────── */

function toggleNav() {
    const links = document.querySelector(".nav-links");
    if (links) links.classList.toggle("active");
}

/* ── Notifications ─────────────────────────────────────────────────── */

function showNotification(message, type) {
    const existing = document.querySelector(".notification");
    if (existing) existing.remove();

    const colors = {
        success: "var(--green)",
        error: "var(--red)",
        warning: "var(--yellow)",
        info: "var(--accent)",
    };

    const el = document.createElement("div");
    el.className = "notification";
    el.style.cssText = `
        position: fixed; top: 1rem; right: 1rem; z-index: 1000;
        padding: 0.75rem 1.25rem; border-radius: 6px;
        background: var(--surface); border: 1px solid ${colors[type] || colors.info};
        color: var(--text-bright); font-size: 0.9rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        animation: slideIn 0.3s ease;
    `;
    el.textContent = message;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 3500);
}

/* ── Utilities ─────────────────────────────────────────────────────── */

function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}

function metricRow(label, value) {
    return `<div class="metric-item"><span class="metric-label">${label}</span><span class="metric-val">${value}</span></div>`;
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.appendChild(document.createTextNode(text || ""));
    return div.innerHTML;
}

/* ── CSS animation keyframe (injected) ─────────────────────────────── */

(function() {
    const style = document.createElement("style");
    style.textContent = `@keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }`;
    document.head.appendChild(style);
})();
