/**
 * Template Manager Module
 * Handles prompt templates and their rendering
 */
class TemplateManager {
    constructor() {
        this.app = null;
        this.promptTemplates = [
            {
                id: "short",
                name: "Short & sweet",
                text: "Get the open GitHub issues for my next sprint backlog."
            },
            {
                id: "repo_minimal",
                name: "Repo + minimal filters (recommended)",
                text: `From {owner_repo}, collect OPEN issues (exclude PRs) updated in the last 30 days for the next sprint backlog.
Prioritize by priority label (P0, P1, P2), then by updated_at.
Include title, #number, labels, updated_at, url and a 1-sentence summary per issue.`
            },
            {
                id: "sprint_window_capacity",
                name: "Sprint window + capacity",
                text: `From {owner_repo}, propose a next sprint backlog for {start_date}–{end_date} with roughly {capacity_points} story points.
Use OPEN issues only; prefer labels feature, bug, chore. Include estimate (if present), priority, and dependencies/blockers inferred from comments.`
            },
            {
                id: "labels_exclusions",
                name: "Labels & exclusions",
                text: `Build the next sprint backlog from {owner_repo} using OPEN issues with labels in {selected_labels} and excluding {exclude_labels}.
De-dupe near-duplicates, split multi-work items into sub-tasks, and order by P0→P1→P2, then updated_at.`
            },
            {
                id: "milestone",
                name: "Milestone aware",
                text: `For {owner_repo}, assemble OPEN issues suitable for the "{milestone_name}" milestone as the next sprint backlog.
Show #number, title, labels, estimate/points, assignee, last activity, url, and a one-line "why now".`
            },
            {
                id: "comments_informed",
                name: "Comments-informed prioritization",
                text: `From {owner_repo}, create a next sprint backlog of OPEN issues.
Use the latest issue comments to surface blockers, design links, acceptance criteria and summarize them in ≤2 lines per item.
Prioritize P0 and items with clear acceptance criteria.`
            },
            {
                id: "json_schema",
                name: "Output format (JSON schema)",
                text: `From {owner_repo}, return a next sprint backlog of OPEN issues. For each item:
{ "number": n, "title": "...", "priority": "P0|P1|P2|none", "labels": [], "estimate": "n|unknown", "updated_at": "ISO", "url": "...", "summary": "≤25 words", "blockers": "≤15 words" }.
Order by priority then updated_at.`
            },
            {
                id: "concrete_repo",
                name: "Concrete example (from Settings repo)",
                text: `From {owner_repo}, build the next sprint backlog of OPEN issues (exclude PRs).
Include #number, title, labels, updated_at, url and a one-line summary per issue; if comments exist, add blockers/next step in ≤15 words. Sort by P0→P1→P2, then updated_at desc.`
            },
            {
                id: "capacity_quickwins",
                name: "Capacity + quick wins",
                text: `From {owner_repo}, pick OPEN issues for next sprint with mix: 60% quick wins (<1 day), 40% medium (1–3 days).
Show #number, title, est, labels, url, and 1-line "why it fits now". Prioritize customer impact and unblockers.`
            },
            {
                id: "grooming",
                name: "Backlog grooming tone",
                text: `Groom the next sprint backlog from {owner_repo} (OPEN issues only). Flag duplicates, suggest label fixes, and propose top 10 in execution order with a crisp next action each.`
            },
            {
                id: "research_papers",
                name: "Research Paper Analysis",
                text: `Analyze GitHub issues from {owner_repo} and match them with relevant AI research papers. Provide:
1. Key requirements extracted from GitHub issues
2. Relevant research papers that address these requirements
3. Implementation recommendations based on research findings
4. Gap analysis and potential research opportunities`
            },
            {
                id: "literature_review",
                name: "Literature Review",
                text: `Conduct a literature review using GitHub issues from {owner_repo} and research papers. Focus on:
1. Current state of the field based on GitHub discussions
2. Relevant research papers and their contributions
3. Research gaps identified from GitHub issues
4. Future research directions and collaboration opportunities`
            },
            {
                id: "implementation_guide",
                name: "Implementation Guide",
                text: `Create an implementation guide by combining GitHub issues from {owner_repo} with research paper insights. Include:
1. Technical requirements from GitHub issues
2. Recommended approaches from research papers
3. Architecture and design patterns
4. Potential challenges and mitigation strategies`
            }
        ];
    }

    /**
     * Set reference to main app instance
     */
    setApp(app) {
        this.app = app;
    }

    /**
     * Populate prompt templates dropdown
     */
    populatePromptTemplates() {
        const select = document.getElementById('promptTemplate');
        if (!select) return;

        select.innerHTML = '';
        this.promptTemplates.forEach(template => {
            const option = document.createElement('option');
            option.value = template.id;
            option.textContent = template.name;
            select.appendChild(option);
        });

        select.value = 'repo_minimal';
        this.renderPromptPreview();
    }

    /**
     * Bind prompt template UI events
     */
    bindPromptTemplateUI() {
        // Populate template dropdown first
        this.populateTemplateDropdown();
        
        const select = document.getElementById('promptTemplate');
        const inputs = ['#tpl_sprint_len', '#tpl_capacity', '#tpl_labels_include', '#tpl_labels_exclude', '#tpl_milestone'];

        if (select) {
            select.addEventListener('change', () => this.renderPromptPreview());
        }

        inputs.forEach(selector => {
            const element = document.querySelector(selector);
            if (element) {
                element.addEventListener('input', () => this.renderPromptPreview());
            }
        });

        const copyBtn = document.getElementById('btnCopyPrompt');
        if (copyBtn) {
            copyBtn.addEventListener('click', async () => {
                const text = this.getFormValue('#previewPrompt') || this.fillPromptTemplate(this.getFormValue('#promptTemplate'), this.app.getSettings());
                
                // Use ChatManager's setUserPrompt method to update context window info
                if (this.app && this.app.chatManager) {
                    this.app.chatManager.setUserPrompt(text);
                } else {
                    // Fallback to direct form value setting
                    this.setFormValue('#userPrompt', text);
                }
                
                try {
                    await navigator.clipboard.writeText(text);
                    this.setFormValue('#copyStatus', 'Copied to clipboard & Chat → User Prompt');
                    setTimeout(() => this.setFormValue('#copyStatus', ''), 2000);
                } catch {
                    this.setFormValue('#copyStatus', 'Copied to Chat → User Prompt (clipboard blocked)');
                    setTimeout(() => this.setFormValue('#copyStatus', ''), 2000);
                }
                
                this.app.activateTab('chat');
            });
        }
    }

    /**
     * Populate template dropdown with available templates
     */
    populateTemplateDropdown() {
        const select = document.getElementById('promptTemplate');
        if (!select) return;

        select.innerHTML = '';
        
        this.promptTemplates.forEach(template => {
            const option = document.createElement('option');
            option.value = template.id;
            option.textContent = template.name;
            select.appendChild(option);
        });

        // Set default selection
        if (select.options.length > 0) {
            select.value = select.options[0].value;
            this.renderPromptPreview();
        }
    }

    /**
     * Render prompt preview
     */
    renderPromptPreview() {
        const templateId = this.getFormValue('#promptTemplate');
        const text = this.fillPromptTemplate(templateId, this.app.getSettings());
        this.setFormValue('#previewPrompt', text);
    }

    /**
     * Fill prompt template with values
     */
    fillPromptTemplate(templateId, settings) {
        const template = this.promptTemplates.find(t => t.id === templateId) || this.promptTemplates[0];
        const repo = (settings?.mcp?.github?.repo || "").trim();
        
        if (!repo || !repo.includes('/')) {
            return "Get the open GitHub issues for my next sprint backlog.  <!-- Tip: set owner/repo in Settings → MCP GitHub -->";
        }

        const sprintLen = parseInt(this.getFormValue('#tpl_sprint_len') || '14', 10);
        const capacity = parseInt(this.getFormValue('#tpl_capacity') || '20', 10);

        const includeLabels = this.csvToArray(this.getFormValue('#tpl_labels_include')).map(x => x.replaceAll('"', ''));
        const excludeLabels = this.csvToArray(this.getFormValue('#tpl_labels_exclude')).map(x => x.replaceAll('"', ''));
        const milestone = (this.getFormValue('#tpl_milestone') || "Next Sprint").trim();

        const start = this.nextMonday();
        const end = this.addDays(start, sprintLen - 1);

        const context = {
            "{owner_repo}": repo,
            "{start_date}": this.isoDate(start),
            "{end_date}": this.isoDate(end),
            "{capacity_points}": String(capacity),
            "{selected_labels}": JSON.stringify(includeLabels.length ? includeLabels : ["feature", "bug", "chore"]),
            "{exclude_labels}": JSON.stringify(excludeLabels.length ? excludeLabels : ["wontfix", "duplicate"]),
            "{milestone_name}": milestone || "Next Sprint",
        };

        let output = template.text;
        Object.entries(context).forEach(([key, value]) => {
            output = output.split(key).join(value);
        });
        
        return output;
    }

    /**
     * Helper: Get next Monday
     */
    nextMonday(date = new Date()) {
        const dt = new Date(date);
        const day = dt.getDay();
        const diff = (8 - (day || 7)) % 7;
        dt.setDate(dt.getDate() + (diff === 0 ? 7 : diff));
        dt.setHours(0, 0, 0, 0);
        return dt;
    }

    /**
     * Helper: Add days to date
     */
    addDays(date, days) {
        const dt = new Date(date);
        dt.setDate(dt.getDate() + days);
        return dt;
    }

    /**
     * Helper: Format date as ISO
     */
    isoDate(date) {
        const y = date.getFullYear();
        const m = String(date.getMonth() + 1).padStart(2, '0');
        const d = String(date.getDate()).padStart(2, '0');
        return `${y}-${m}-${d}`;
    }

    /**
     * Helper: Convert CSV string to array
     */
    csvToArray(str) {
        return (str || "")
            .split(",")
            .map(x => x.trim())
            .filter(Boolean);
    }

    /**
     * Helper: Get form value
     */
    getFormValue(selector) {
        const element = document.querySelector(selector);
        return element ? element.value : '';
    }

    /**
     * Helper: Set form value
     */
    setFormValue(selector, value) {
        const element = document.querySelector(selector);
        if (element) {
            element.value = value;
        }
    }
}

// Export for use in other modules
window.TemplateManager = TemplateManager;
