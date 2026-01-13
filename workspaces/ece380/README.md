# Workspace Template

This is a workspace template for organizing course materials, projects, and agent configurations.

## Structure

- **sources/** - Upload course materials, PDFs, notes, assignments here
- **index/** - Generated indices (file listings, previews, search indexes)
- **agents/** - Agent profiles and configurations for this workspace

## Usage

1. Create a new workspace from this template:
   ```powershell
   .\scripts\workspace_new.ps1 -Name ece380
   ```

2. Add source documents to `sources/`:
   - PDFs (lecture notes, textbooks)
   - Markdown files (assignments, notes)
   - Code files (examples, starter code)

3. Index the workspace:
   ```powershell
   .\scripts\workspace_index.ps1 -Workspace ece380
   ```

4. Agent profiles control what each agent can do:
   - Read-only: explain, analyze, generate questions
   - Patch-capable: modify code, create PRs (restricted)
   - Quality-gated: run after modifications

## Agents in this workspace

See `agents/` for available agent profiles. Each defines:
- What the agent can read
- What actions it's allowed to take
- System prompt and guardrails
