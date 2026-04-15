# Tombstoned Components Report

**Total flagged:** 100 components

These components were automatically flagged during ingestion because they contain
suspicious patterns (arbitrary code execution, secret exfiltration, permission bypass,
etc.). They are excluded from search results and recommendations.

To un-tombstone a component, manually update the database:
```sql
UPDATE components SET tombstoned = 0, tombstone_reason = NULL WHERE id = <id>;
```

---

## Archon (2 flagged)

### docker-extend (skill)
- **File:** `.claude/skills/docker-extend/SKILL.md`
- **Last author:** Leex
- **Last commit:** 2026-04-05
- **Findings:**
  - [CRITICAL] rm -rf targeting root, home, or $HOME — destructive filesystem operation

### test-release (skill)
- **File:** `.claude/skills/test-release/SKILL.md`
- **Last author:** Rasmus Widing
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] curl piped to bash — remote code execution
  - [WARNING] Reference to ANTHROPIC_API_KEY

## Claude-Code-Workflow (5 flagged)

### cli-lite-planning-agent (agent)
- **File:** `.claude/agents/cli-lite-planning-agent.md`
- **Last author:** catlog22
- **Last commit:** 2026-04-12
- **Findings:**
  - [CRITICAL] exec() call detected — arbitrary code execution

### cli-planning-agent (agent)
- **File:** `.claude/agents/cli-planning-agent.md`
- **Last author:** catlog22
- **Last commit:** 2026-03-20
- **Findings:**
  - [CRITICAL] exec() call detected — arbitrary code execution

### cli-roadmap-plan-agent (agent)
- **File:** `.claude/agents/cli-roadmap-plan-agent.md`
- **Last author:** catlog22
- **Last commit:** 2026-02-17
- **Findings:**
  - [CRITICAL] exec() call detected — arbitrary code execution

### issue-plan-agent (agent)
- **File:** `.claude/agents/issue-plan-agent.md`
- **Last author:** catlog22
- **Last commit:** 2026-04-12
- **Findings:**
  - [CRITICAL] exec() call detected — arbitrary code execution

### test-action-planning-agent (agent)
- **File:** `.claude/agents/test-action-planning-agent.md`
- **Last author:** catlog22
- **Last commit:** 2026-04-12
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution

## agentic-qe (14 flagged)

### Hooks Automation (skill)
- **File:** `.claude/skills/hooks-automation/SKILL.md`
- **Last author:** Profa
- **Last commit:** 2025-10-20
- **Findings:**
  - [CRITICAL] rm -rf targeting root, home, or $HOME — destructive filesystem operation

### n8n-expression-testing (skill)
- **File:** `.claude/skills/n8n-expression-testing/SKILL.md`
- **Last author:** Dragan Spiridonov
- **Last commit:** 2026-03-17
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution
  - [CRITICAL] exec() call detected — arbitrary code execution

### n8n-security-testing (skill)
- **File:** `.claude/skills/n8n-security-testing/SKILL.md`
- **Last author:** Dragan Spiridonov
- **Last commit:** 2026-03-17
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution
  - [CRITICAL] exec() call detected — arbitrary code execution

### pentest-validation (skill)
- **File:** `.claude/skills/pentest-validation/SKILL.md`
- **Last author:** Dragan Spiridonov
- **Last commit:** 2026-03-18
- **Findings:**
  - [CRITICAL] exec() call detected — arbitrary code execution
  - [WARNING] Direct IP address URL — potential C2 or exfiltration endpoint

### release (skill)
- **File:** `.claude/skills/release/SKILL.md`
- **Last author:** Dragan Spiridonov
- **Last commit:** 2026-04-13
- **Findings:**
  - [CRITICAL] rm -rf targeting root, home, or $HOME — destructive filesystem operation

### security-watch (skill)
- **File:** `.claude/skills/security-watch/SKILL.md`
- **Last author:** Dragan Spiridonov
- **Last commit:** 2026-03-18
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution

### qcsd-development-swarm (skill)
- **File:** `.kiro/skills/qcsd-development-swarm/SKILL.md`
- **Last author:** Dragan Spiridonov
- **Last commit:** 2026-03-24
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution

### qe-n8n-expression-testing (skill)
- **File:** `.kiro/skills/qe-n8n-expression-testing/SKILL.md`
- **Last author:** Lalit
- **Last commit:** 2026-02-25
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution
  - [CRITICAL] exec() call detected — arbitrary code execution

### qe-n8n-security-testing (skill)
- **File:** `.kiro/skills/qe-n8n-security-testing/SKILL.md`
- **Last author:** Lalit
- **Last commit:** 2026-02-25
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution
  - [CRITICAL] exec() call detected — arbitrary code execution

### qe-pentest-validation (skill)
- **File:** `.kiro/skills/qe-pentest-validation/SKILL.md`
- **Last author:** Dragan Spiridonov
- **Last commit:** 2026-03-11
- **Findings:**
  - [CRITICAL] exec() call detected — arbitrary code execution
  - [WARNING] Direct IP address URL — potential C2 or exfiltration endpoint

### n8n-expression-testing (skill)
- **File:** `assets/skills/n8n-expression-testing/SKILL.md`
- **Last author:** Dragan Spiridonov
- **Last commit:** 2026-03-17
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution
  - [CRITICAL] exec() call detected — arbitrary code execution

### n8n-security-testing (skill)
- **File:** `assets/skills/n8n-security-testing/SKILL.md`
- **Last author:** Dragan Spiridonov
- **Last commit:** 2026-03-17
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution
  - [CRITICAL] exec() call detected — arbitrary code execution

### pentest-validation (skill)
- **File:** `assets/skills/pentest-validation/SKILL.md`
- **Last author:** Dragan Spiridonov
- **Last commit:** 2026-03-18
- **Findings:**
  - [CRITICAL] exec() call detected — arbitrary code execution
  - [WARNING] Direct IP address URL — potential C2 or exfiltration endpoint

### security-watch (skill)
- **File:** `assets/skills/security-watch/SKILL.md`
- **Last author:** Dragan Spiridonov
- **Last commit:** 2026-03-18
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution

## agents (1 flagged)

### code-review-excellence (skill)
- **File:** `plugins/developer-essentials/skills/code-review-excellence/SKILL.md`
- **Last author:** Seth Hobson
- **Last commit:** 2026-03-07
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution

## antigravity-awesome-skills (77 flagged)

### 007 (skill)
- **File:** `plugins/antigravity-awesome-skills-claude/skills/007/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution
  - [CRITICAL] exec() call detected — arbitrary code execution

### apify-actor-development (skill)
- **File:** `plugins/antigravity-awesome-skills-claude/skills/apify-actor-development/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution
  - [CRITICAL] curl piped to bash — remote code execution

### aws-penetration-testing (skill)
- **File:** `plugins/antigravity-awesome-skills-claude/skills/aws-penetration-testing/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-03-29
- **Findings:**
  - [CRITICAL] HTTP request containing sensitive env var — potential exfiltration
  - [WARNING] Reference to AWS_SECRET
  - [WARNING] Direct IP address URL — potential C2 or exfiltration endpoint

### bun-development (skill)
- **File:** `plugins/antigravity-awesome-skills-claude/skills/bun-development/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] curl piped to bash — remote code execution

### chrome-extension-developer (skill)
- **File:** `plugins/antigravity-awesome-skills-claude/skills/chrome-extension-developer/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution

### cloud-penetration-testing (skill)
- **File:** `plugins/antigravity-awesome-skills-claude/skills/cloud-penetration-testing/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-03-29
- **Findings:**
  - [CRITICAL] curl piped to bash — remote code execution
  - [CRITICAL] HTTP request containing sensitive env var — potential exfiltration
  - [WARNING] Direct IP address URL — potential C2 or exfiltration endpoint

### codebase-audit-pre-push (skill)
- **File:** `plugins/antigravity-awesome-skills-claude/skills/codebase-audit-pre-push/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] exec() call detected — arbitrary code execution

### electron-development (skill)
- **File:** `plugins/antigravity-awesome-skills-claude/skills/electron-development/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-03-27
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution

### evolution (skill)
- **File:** `plugins/antigravity-awesome-skills-claude/skills/evolution/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] curl piped to bash — remote code execution

### gcp-cloud-run (skill)
- **File:** `plugins/antigravity-awesome-skills-claude/skills/gcp-cloud-run/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] rm -rf targeting root, home, or $HOME — destructive filesystem operation

### github-workflow-automation (skill)
- **File:** `plugins/antigravity-awesome-skills-claude/skills/github-workflow-automation/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] exec() call detected — arbitrary code execution
  - [WARNING] Reference to ANTHROPIC_API_KEY

### hugging-face-papers (skill)
- **File:** `plugins/antigravity-awesome-skills-claude/skills/hugging-face-papers/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] HTTP request containing sensitive env var — potential exfiltration

### langgraph (skill)
- **File:** `plugins/antigravity-awesome-skills-claude/skills/langgraph/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution

### linux-privilege-escalation (skill)
- **File:** `plugins/antigravity-awesome-skills-claude/skills/linux-privilege-escalation/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-03-29
- **Findings:**
  - [CRITICAL] exec() call detected — arbitrary code execution
  - [CRITICAL] /dev/tcp/ — bash network socket — potential data exfiltration

### loki-mode (skill)
- **File:** `plugins/antigravity-awesome-skills-claude/skills/loki-mode/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-03-27
- **Findings:**
  - [CRITICAL] --dangerously-skip-permissions flag — bypasses safety controls

### makepad-splash (skill)
- **File:** `plugins/antigravity-awesome-skills-claude/skills/makepad-splash/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution

### personal-tool-builder (skill)
- **File:** `plugins/antigravity-awesome-skills-claude/skills/personal-tool-builder/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] exec() call detected — arbitrary code execution

### semgrep-rule-creator (skill)
- **File:** `plugins/antigravity-awesome-skills-claude/skills/semgrep-rule-creator/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution

### telegram (skill)
- **File:** `plugins/antigravity-awesome-skills-claude/skills/telegram/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] HTTP request containing sensitive env var — potential exfiltration

### varlock (skill)
- **File:** `plugins/antigravity-awesome-skills-claude/skills/varlock/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] exec() call detected — arbitrary code execution
  - [CRITICAL] HTTP request containing sensitive env var — potential exfiltration

### vibe-code-auditor (skill)
- **File:** `plugins/antigravity-awesome-skills-claude/skills/vibe-code-auditor/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution
  - [CRITICAL] exec() call detected — arbitrary code execution

### vulnerability-scanner (skill)
- **File:** `plugins/antigravity-awesome-skills-claude/skills/vulnerability-scanner/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution
  - [CRITICAL] exec() call detected — arbitrary code execution

### wordpress-penetration-testing (skill)
- **File:** `plugins/antigravity-awesome-skills-claude/skills/wordpress-penetration-testing/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-03-29
- **Findings:**
  - [CRITICAL] exec() call detected — arbitrary code execution
  - [WARNING] Direct IP address URL — potential C2 or exfiltration endpoint
  - [CRITICAL] /dev/tcp/ — bash network socket — potential data exfiltration

### xss-html-injection (skill)
- **File:** `plugins/antigravity-awesome-skills-claude/skills/xss-html-injection/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-03-29
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution

### 007 (skill)
- **File:** `plugins/antigravity-awesome-skills/skills/007/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution
  - [CRITICAL] exec() call detected — arbitrary code execution

### apify-actor-development (skill)
- **File:** `plugins/antigravity-awesome-skills/skills/apify-actor-development/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution
  - [CRITICAL] curl piped to bash — remote code execution

### aws-penetration-testing (skill)
- **File:** `plugins/antigravity-awesome-skills/skills/aws-penetration-testing/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-03-29
- **Findings:**
  - [CRITICAL] HTTP request containing sensitive env var — potential exfiltration
  - [WARNING] Reference to AWS_SECRET
  - [WARNING] Direct IP address URL — potential C2 or exfiltration endpoint

### bun-development (skill)
- **File:** `plugins/antigravity-awesome-skills/skills/bun-development/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] curl piped to bash — remote code execution

### chrome-extension-developer (skill)
- **File:** `plugins/antigravity-awesome-skills/skills/chrome-extension-developer/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution

### cloud-penetration-testing (skill)
- **File:** `plugins/antigravity-awesome-skills/skills/cloud-penetration-testing/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-03-29
- **Findings:**
  - [CRITICAL] curl piped to bash — remote code execution
  - [CRITICAL] HTTP request containing sensitive env var — potential exfiltration
  - [WARNING] Direct IP address URL — potential C2 or exfiltration endpoint

### codebase-audit-pre-push (skill)
- **File:** `plugins/antigravity-awesome-skills/skills/codebase-audit-pre-push/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] exec() call detected — arbitrary code execution

### electron-development (skill)
- **File:** `plugins/antigravity-awesome-skills/skills/electron-development/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-03-27
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution

### evolution (skill)
- **File:** `plugins/antigravity-awesome-skills/skills/evolution/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] curl piped to bash — remote code execution

### gcp-cloud-run (skill)
- **File:** `plugins/antigravity-awesome-skills/skills/gcp-cloud-run/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] rm -rf targeting root, home, or $HOME — destructive filesystem operation

### github-workflow-automation (skill)
- **File:** `plugins/antigravity-awesome-skills/skills/github-workflow-automation/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] exec() call detected — arbitrary code execution
  - [WARNING] Reference to ANTHROPIC_API_KEY

### hugging-face-papers (skill)
- **File:** `plugins/antigravity-awesome-skills/skills/hugging-face-papers/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] HTTP request containing sensitive env var — potential exfiltration

### langgraph (skill)
- **File:** `plugins/antigravity-awesome-skills/skills/langgraph/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution

### linux-privilege-escalation (skill)
- **File:** `plugins/antigravity-awesome-skills/skills/linux-privilege-escalation/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-03-29
- **Findings:**
  - [CRITICAL] exec() call detected — arbitrary code execution
  - [CRITICAL] /dev/tcp/ — bash network socket — potential data exfiltration

### makepad-splash (skill)
- **File:** `plugins/antigravity-awesome-skills/skills/makepad-splash/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution

### personal-tool-builder (skill)
- **File:** `plugins/antigravity-awesome-skills/skills/personal-tool-builder/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] exec() call detected — arbitrary code execution

### semgrep-rule-creator (skill)
- **File:** `plugins/antigravity-awesome-skills/skills/semgrep-rule-creator/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution

### telegram (skill)
- **File:** `plugins/antigravity-awesome-skills/skills/telegram/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] HTTP request containing sensitive env var — potential exfiltration

### vibe-code-auditor (skill)
- **File:** `plugins/antigravity-awesome-skills/skills/vibe-code-auditor/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution
  - [CRITICAL] exec() call detected — arbitrary code execution

### vulnerability-scanner (skill)
- **File:** `plugins/antigravity-awesome-skills/skills/vulnerability-scanner/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution
  - [CRITICAL] exec() call detected — arbitrary code execution

### wordpress-penetration-testing (skill)
- **File:** `plugins/antigravity-awesome-skills/skills/wordpress-penetration-testing/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-03-29
- **Findings:**
  - [CRITICAL] exec() call detected — arbitrary code execution
  - [WARNING] Direct IP address URL — potential C2 or exfiltration endpoint
  - [CRITICAL] /dev/tcp/ — bash network socket — potential data exfiltration

### xss-html-injection (skill)
- **File:** `plugins/antigravity-awesome-skills/skills/xss-html-injection/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-03-29
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution

### langgraph (skill)
- **File:** `plugins/antigravity-bundle-agent-architect/skills/langgraph/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution

### cloud-penetration-testing (skill)
- **File:** `plugins/antigravity-bundle-security-engineer/skills/cloud-penetration-testing/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-03-29
- **Findings:**
  - [CRITICAL] curl piped to bash — remote code execution
  - [CRITICAL] HTTP request containing sensitive env var — potential exfiltration
  - [WARNING] Direct IP address URL — potential C2 or exfiltration endpoint

### linux-privilege-escalation (skill)
- **File:** `plugins/antigravity-bundle-security-engineer/skills/linux-privilege-escalation/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-03-29
- **Findings:**
  - [CRITICAL] exec() call detected — arbitrary code execution
  - [CRITICAL] /dev/tcp/ — bash network socket — potential data exfiltration

### vulnerability-scanner (skill)
- **File:** `plugins/antigravity-bundle-security-engineer/skills/vulnerability-scanner/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution
  - [CRITICAL] exec() call detected — arbitrary code execution

### 007 (skill)
- **File:** `skills/007/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution
  - [CRITICAL] exec() call detected — arbitrary code execution

### apify-actor-development (skill)
- **File:** `skills/apify-actor-development/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution
  - [CRITICAL] curl piped to bash — remote code execution

### audit-skills (skill)
- **File:** `skills/audit-skills/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] curl piped to bash — remote code execution
  - [CRITICAL] rm -rf targeting root, home, or $HOME — destructive filesystem operation

### aws-penetration-testing (skill)
- **File:** `skills/aws-penetration-testing/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-03-29
- **Findings:**
  - [CRITICAL] HTTP request containing sensitive env var — potential exfiltration
  - [WARNING] Reference to AWS_SECRET
  - [WARNING] Direct IP address URL — potential C2 or exfiltration endpoint

### bun-development (skill)
- **File:** `skills/bun-development/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] curl piped to bash — remote code execution

### chrome-extension-developer (skill)
- **File:** `skills/chrome-extension-developer/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution

### claude-code-expert (skill)
- **File:** `skills/claude-code-expert/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] curl piped to bash — remote code execution
  - [WARNING] Reference to ANTHROPIC_API_KEY
  - [CRITICAL] --dangerously-skip-permissions flag — bypasses safety controls

### claude-in-chrome-troubleshooting (skill)
- **File:** `skills/claude-in-chrome-troubleshooting/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] rm -rf targeting root, home, or $HOME — destructive filesystem operation

### cloud-penetration-testing (skill)
- **File:** `skills/cloud-penetration-testing/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-03-29
- **Findings:**
  - [CRITICAL] curl piped to bash — remote code execution
  - [CRITICAL] HTTP request containing sensitive env var — potential exfiltration
  - [WARNING] Direct IP address URL — potential C2 or exfiltration endpoint

### codebase-audit-pre-push (skill)
- **File:** `skills/codebase-audit-pre-push/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] exec() call detected — arbitrary code execution

### electron-development (skill)
- **File:** `skills/electron-development/SKILL.md`
- **Last author:** Matheus Messias
- **Last commit:** 2026-03-13
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution

### evolution (skill)
- **File:** `skills/evolution/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] curl piped to bash — remote code execution

### gcp-cloud-run (skill)
- **File:** `skills/gcp-cloud-run/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] rm -rf targeting root, home, or $HOME — destructive filesystem operation

### github-workflow-automation (skill)
- **File:** `skills/github-workflow-automation/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] exec() call detected — arbitrary code execution
  - [WARNING] Reference to ANTHROPIC_API_KEY

### hugging-face-papers (skill)
- **File:** `skills/hugging-face-papers/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] HTTP request containing sensitive env var — potential exfiltration

### langgraph (skill)
- **File:** `skills/langgraph/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution

### linux-privilege-escalation (skill)
- **File:** `skills/linux-privilege-escalation/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-03-29
- **Findings:**
  - [CRITICAL] exec() call detected — arbitrary code execution
  - [CRITICAL] /dev/tcp/ — bash network socket — potential data exfiltration

### loki-mode (skill)
- **File:** `skills/loki-mode/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-03-20
- **Findings:**
  - [CRITICAL] --dangerously-skip-permissions flag — bypasses safety controls

### makepad-splash (skill)
- **File:** `skills/makepad-splash/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution

### personal-tool-builder (skill)
- **File:** `skills/personal-tool-builder/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] exec() call detected — arbitrary code execution

### semgrep-rule-creator (skill)
- **File:** `skills/semgrep-rule-creator/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution

### telegram (skill)
- **File:** `skills/telegram/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] HTTP request containing sensitive env var — potential exfiltration

### varlock (skill)
- **File:** `skills/varlock/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] exec() call detected — arbitrary code execution
  - [CRITICAL] HTTP request containing sensitive env var — potential exfiltration

### vibe-code-auditor (skill)
- **File:** `skills/vibe-code-auditor/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution
  - [CRITICAL] exec() call detected — arbitrary code execution

### vulnerability-scanner (skill)
- **File:** `skills/vulnerability-scanner/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-04-14
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution
  - [CRITICAL] exec() call detected — arbitrary code execution

### wordpress-penetration-testing (skill)
- **File:** `skills/wordpress-penetration-testing/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-03-29
- **Findings:**
  - [CRITICAL] exec() call detected — arbitrary code execution
  - [WARNING] Direct IP address URL — potential C2 or exfiltration endpoint
  - [CRITICAL] /dev/tcp/ — bash network socket — potential data exfiltration

### xss-html-injection (skill)
- **File:** `skills/xss-html-injection/SKILL.md`
- **Last author:** sickn33
- **Last commit:** 2026-03-29
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution

## awesome-claude-code-toolkit (1 flagged)

### redis-patterns (skill)
- **File:** `skills/redis-patterns/SKILL.md`
- **Last author:** Rohit Ghumare
- **Last commit:** 2026-02-04
- **Findings:**
  - [CRITICAL] eval() call detected — arbitrary code execution
  - [CRITICAL] exec() call detected — arbitrary code execution
