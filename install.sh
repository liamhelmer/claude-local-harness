#!/usr/bin/env bash
# install.sh — Clone or update all source repositories for the catalog plugin.
#
# Usage:
#   ./install.sh              # Clone missing repos, pull existing ones
#   ./install.sh --pull-only  # Only pull existing repos, don't clone new ones

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPOS_DIR="${SCRIPT_DIR}/repositories"

mkdir -p "${REPOS_DIR}"

# Repository list: URL → directory name
declare -A REPOS=(
	["https://github.com/alirezarezvani/claude-skills.git"]="claude-skills"
	["https://github.com/automazeio/ccpm.git"]="ccpm"
	["https://github.com/BloopAI/vibe-kanban.git"]="vibe-kanban"
	["https://github.com/catlog22/Claude-Code-Workflow.git"]="Claude-Code-Workflow"
	["https://github.com/coleam00/Archon.git"]="Archon"
	["https://github.com/ComposioHQ/awesome-claude-skills.git"]="awesome-claude-skills"
	["https://github.com/czlonkowski/n8n-skills.git"]="n8n-skills"
	["https://github.com/e2b-dev/awesome-ai-agents.git"]="awesome-ai-agents"
	["https://github.com/hesreallyhim/awesome-claude-code.git"]="awesome-claude-code"
	["https://github.com/PenguinAlleyApps/paco-framework.git"]="paco-framework"
	["https://github.com/PeonPing/peon-ping.git"]="peon-ping"
	["https://github.com/Piebald-AI/claude-code-system-prompts.git"]="claude-code-system-prompts"
	["https://github.com/proffesor-for-testing/agentic-qe.git"]="agentic-qe"
	["https://github.com/rohitg00/awesome-claude-code-toolkit.git"]="awesome-claude-code-toolkit"
	["https://github.com/ruvnet/ruflo.git"]="ruflo"
	["https://github.com/ryoppippi/ccusage.git"]="ccusage"
	["https://github.com/shanraisshan/claude-code-best-practice.git"]="claude-code-best-practice"
	["https://github.com/Shpigford/chops.git"]="chops"
	["https://github.com/Shubhamsaboo/awesome-llm-apps.git"]="awesome-llm-apps"
	["https://github.com/sickn33/antigravity-awesome-skills.git"]="antigravity-awesome-skills"
	["https://github.com/thedotmack/claude-mem.git"]="claude-mem"
	["https://github.com/VoltAgent/awesome-claude-code-subagents.git"]="awesome-claude-code-subagents"
	["https://github.com/winfunc/opcode.git"]="opcode"
	["https://github.com/wshobson/agents.git"]="agents"
	["https://github.com/Yeachan-Heo/oh-my-claudecode.git"]="oh-my-claudecode"
	["https://github.com/zilliztech/claude-context.git"]="claude-context"
)

PULL_ONLY=false
if [[ "${1:-}" == "--pull-only" ]]; then
	PULL_ONLY=true
fi

cloned=0
pulled=0
failed=0

for url in "${!REPOS[@]}"; do
	dir="${REPOS[$url]}"
	target="${REPOS_DIR}/${dir}"

	if [[ -d "${target}/.git" ]]; then
		echo "Pulling ${dir}..."
		if git -C "${target}" pull --ff-only --quiet 2>/dev/null; then
			pulled=$((pulled + 1))
		else
			echo "  Warning: pull failed for ${dir}, trying rebase..."
			if git -C "${target}" pull --rebase --quiet 2>/dev/null; then
				pulled=$((pulled + 1))
			else
				echo "  Error: could not update ${dir}"
				failed=$((failed + 1))
			fi
		fi
	elif [[ "${PULL_ONLY}" == true ]]; then
		echo "Skipping ${dir} (not cloned, --pull-only mode)"
	else
		echo "Cloning ${dir}..."
		if git clone --quiet "${url}" "${target}" 2>/dev/null; then
			cloned=$((cloned + 1))
		else
			echo "  Error: clone failed for ${url}"
			failed=$((failed + 1))
		fi
	fi
done

echo ""
echo "--- Install Complete ---"
echo "Cloned:  ${cloned}"
echo "Pulled:  ${pulled}"
echo "Failed:  ${failed}"
echo "Total:   ${#REPOS[@]} repositories"
