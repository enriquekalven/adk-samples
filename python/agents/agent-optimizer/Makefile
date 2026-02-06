# ==============================================================================
# Installation & Setup
# ==============================================================================

# Install dependencies
install:
	uv sync

# ==============================================================================
# Playground Targets
# ==============================================================================

# Launch local dev playground
playground:
	@echo "==============================================================================="
	@echo "| 🚀 Starting your agent playground...                                        |"
	@echo "|                                                                             |"
	@echo "| 🔍 IMPORTANT: Select the 'agent-optimizer' folder to interact with your agent. |"
	@echo "==============================================================================="
	uv run adk web . --port 8501 --reload_agents

# ==============================================================================
# Backend Deployment Targets
# ==============================================================================

# Deploy the agent remotely to Agent Engine
deploy:
	@echo "Deploying to Vertex AI Agent Engine..."
	@cd .. && uv run --project agent-optimizer adk deploy agent_engine --adk_app=agent_optimizer/agent --staging_bucket=staging.project-maui.appspot.com agent-optimizer/deploy_stage

# ==============================================================================
# Gemini Enterprise Integration
# ==============================================================================

# Register the deployed agent to Gemini Enterprise
register-gemini-enterprise:
	@uvx agent-starter-pack@0.29.4 register-gemini-enterprise

# ==============================================================================
# ==============================================================================
# FinOps & Token Economics
# ==============================================================================

# Token Efficiency Scan
optimizer-audit:
	@echo "Running Token Efficiency Scan..."
	@uv run python -c "from agent_optimizer.tools.finops_tools import optimizer_audit; import os; print(optimizer_audit(os.getcwd()))"

# Strategic Pivot Audit
arch-review:
	@echo "Running Strategic Pivot Audit..."
	@uv run python -c "from agent_optimizer.tools.finops_tools import arch_review; import os; print(arch_review(os.getcwd()))"

# Deep Optimization Audit (Hill Climbing)
audit-deep:
	@echo "Running Deep Optimization Audit (Hill Climbing)..."
	@uv run python -c "from agent_optimizer.tools.finops_tools import audit_deep; print(audit_deep())"

# Auto-Remediation
apply-fixes:
	@echo "Applying FinOps Auto-Remediation..."
	@uv run python -c "from agent_optimizer.tools.remediator import apply_fixes; import os; print(apply_fixes(os.getcwd()))"

# Run tests
test:
	uv sync --dev
	uv run pytest tests/

# Run linting
lint:
	uv sync --dev --extra lint
	uv run codespell
	uv run ruff check .
