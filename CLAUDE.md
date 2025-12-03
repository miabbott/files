# Workspace Organization and Guidelines

This file provides guidance to Claude Code when working with code in this repository.

## Workspace Purpose
This `/var/home/miabbott/workspaces` directory serves as a central workspace for managing multiple projects including:
- Work/company repositories
- Personal/hobby projects
- Open source contributions
- Forks of upstream projects

## Directory Structure

### Git Repository Organization
Git repositories are organized by hostname/organization/project structure:
```
workspaces/
├── github.com/org/project/
├── gitlab.com/org/project/
└── gitlab.cee.redhat.com/org/project/
```

For personal projects, use `github.com/miabbott/<project-name>`.

### Standalone Files
The workspace may contain:
- Scripts and utilities
- Documentation and notes
- Data or output files

### One-Off Projects
When working on one-off projects, Claude should:
1. Ask if a dedicated directory should be created
2. Create directories using kebab-case naming convention
3. Automatically initialize new project directories as git repositories
4. Place dedicated project directories under version control

## File and Directory Naming Conventions
- Use **kebab-case** for all directories and files (e.g., `my-project`, `util-script.py`)

## Git Workflow and Commit Guidelines

### Python Virtual Environment for Git Hooks
Git hooks in this workspace may require Python dependencies (such as `rh_pre_commit`). To ensure hooks function properly:

**Before running git commit commands:**
1. Activate the Python virtual environment located at `/var/home/miabbott/py-git-env`
2. Run git commands within the activated environment

**Example:**
```bash
source /var/home/miabbott/py-git-env/bin/activate
git commit -s -m "Commit message"
```

When using the Bash tool to execute git commits, ensure commands are run with the virtual environment activated.

### Repository Modifications
- **Never modify files in git repositories without explicit permission**
- Always request permission before making changes to checked-out repositories

### Commit Approach
- Commit behavior is context-dependent based on repository type and scope of changes
- **Always ask before committing** - propose commits and wait for approval
- **Always capture significant progress in git commits**

### Commit Proposals
When proposing a commit, Claude should provide:
- The proposed commit message
- A summary of why the commit is needed

### Required Commit Practices

**Always use signed-off commits:**
```bash
git commit -s
```

### Commit Message Format
Follow the guidelines from https://cbea.ms/git-commit/ with additional requirements:

#### The Seven Rules of Great Commit Messages

1. **Separate subject from body with a blank line**
2. **Limit the subject line to 50 characters**
3. **Capitalize the subject line**
4. **Do not end the subject line with a period**
5. **Use the imperative mood in the subject line**
   - Test: "If applied, this commit will _[your subject line]_"
   - Example: "Add feature" not "Added feature"
6. **Wrap the body at 72 characters**
7. **Use the body to explain what and why vs. how**

#### Additional Requirements

8. **Avoid bulleted lists unless absolutely necessary**
   - Bulleted lists are the exception, not the norm
   - Favor detailed but concise prose in the commit body
9. **Avoid overly expressive or emotional language**
   - Keep the language professional and factual
10. **Never use emojis in commit messages**
11. **Always include Claude Code attribution as a git trailer**

#### Commit Message Style Guidelines

- Write in complete sentences and paragraphs
- Focus on explaining the reasoning and context for changes
- Multiple paragraphs are encouraged for complex changes
- Each paragraph should focus on a specific aspect of the change
- Reserve bulleted lists for exceptional cases where a list format truly improves clarity over prose

#### Attribution Format
All commits created by Claude Code must include the following git trailer format:
```
Assisted-by: Claude Code (MODEL_NAME)
```

Where MODEL_NAME indicates the AI model being used. Examples:
- `Assisted-by: Claude Code (Sonnet 4.5)`
- `Assisted-by: Claude Code (Sonnet 3.5)`
- `Assisted-by: Claude Code (Opus)`

The model name is the most important part of the attribution as it captures
which AI model assisted with the commit.

#### Complete Commit Message Template

```
Capitalize, 50 chars or less summary (imperative mood)

Detailed explanatory text wrapped at 72 characters. Write in prose
form using complete sentences. Explain what problem this commit solves
and why this approach was chosen.

For complex changes, use multiple paragraphs to provide additional
context. Each paragraph should focus on a specific aspect of the
change such as the problem being solved, the approach taken, or
important implementation considerations.

Explain the problem that this commit is solving. Focus on why you
are making this change as opposed to how (the code explains that).
Are there side effects or other unintuitive consequences of this
change? Here's the place to explain them.

Reserve bulleted lists for exceptional cases where a list format truly
improves clarity over prose. Keep the language professional and
factual, avoiding overly expressive or emotional phrasing.

Assisted-by: Claude Code (Sonnet 4.5)
Signed-off-by: Your Name <your.email@example.com>
```

### Git Best Practices (Universal)

1. **Commit Related Changes**: Group logically related changes together in a single commit
2. **Commit Often**: Make frequent commits to create a detailed project history
3. **Don't Commit Half-Done Work**: Commits should represent complete, working states
4. **Test Before Committing**: Ensure code works before creating a commit
5. **Write Meaningful Commit Messages**: Follow the guidelines above
6. **Use Branches**: Create feature branches for new work, keep main/master stable
7. **Review Before Committing**: Check `git diff` and `git status` before committing
8. **Don't Commit Generated Files**: Exclude build artifacts, compiled files, and dependencies
9. **Keep Commits Atomic**: Each commit should represent one logical change
10. **Don't Alter Published History**: Avoid rebasing or amending commits that have been pushed to shared branches

## Question Protocol

**Present questions one at a time.** Do not ask multiple questions in a single message. Wait for the user's response before proceeding to the next question.

## Attribution and Sourcing

All output from Claude Code must be attributable to sources:
- User's own responses and instructions
- Input files or documents from the workspace
- External sources fetched from the internet (with URLs provided)

When using external sources, cite them clearly with links or file paths.

## Development Workflow

1. **Session Start:** Ask if creating a new project directory
2. **During Work:** Commit significant progress regularly with proper messages
3. **Before Finishing:** Ensure all meaningful work is committed
4. **Git Hygiene:** Keep commits atomic and well-described

## Working in This Workspace

### General Principles
- Claude Code operates from this workspace directory for most tasks
- Respect the existing organization structure when navigating between projects
- Always seek permission before modifying files in existing git repositories
- Follow the naming conventions and workflow guidelines outlined above
