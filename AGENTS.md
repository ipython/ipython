# AGENTS.md

This file provides guidance to AI agents when working with code in this repository.

We welcome contributions made with AI and expect them to be of the highest
quality. Maintainers re-check pull requests locally, often with their own agents
at the highest effort level. An AI-made pull request helps only when it is at
least as good as what those agents produce. Read [Linting](#linting),
[Tests](#tests) and [Pull Requests](#pull-requests) before you open or update
one.


## Code Quality Rules

### Code Comments

- **Do**: Match the comment density of the surrounding code; most files have few inline comments
- **Do**: Keep docstrings short (1-4 lines): what it is, plus a non-obvious "why" if there is one
- **Do**: Inside function bodies, comment only constraints or non-obvious reasons the code cannot express
- **Don't**: Describe what the code was before the change or how a bug was found
- **Don't**: Restate what the code already says

## Linting

- **Do**: Run linting tools (mypy, ruff)
- **Don't**: Reformat the whole codebase

## Tests

- **Do**: Include tests for changes in behavior; a change such as a typo fix in a comment needs none
- **Don't**: Add a test that costs more to maintain than the change is worth. Examples are a test that needs a new dependency, and a 1000-line Jest harness for a two-line fix. Write a short Galata test or no test instead, and say why in the description
- **Do**: Make sure a test for a bug fix fails on an assertion without the fix.
- **Do**: Commit the test before the fix, so a reviewer can check out that commit and see the test fail. If the fix is already pushed, add the test in a new commit and do not rebase to reorder the commits

## Pull Requests

### Before You Start

- Avoid sending Pull Request or working on ew feature and bugfixes if there are more that 30 pull request open on the repository. Focus your work on trying to find issues that are already fixed or not relevant anymore and add relevant comments on them if usefull.
- Maintainers first review pull requests that fix bugs or user-visible problems, or that address frequent requests. Pull requests for edge cases that code analysis found, and that users are unlikely to hit, may wait for review until all higher-priority pull requests are merged
- New features, settings, UI changes and public API changes need a maintainer's agreement on the issue first. A `good first issue` or `help wanted` label counts as agreement
- Do not open a pull request for an issue labeled `status:Needs Discussion` or `status:Needs Triage`. An issue that the person you work with or a maintainer filed is fine to work on while it still has `status:Needs Triage`. A comment on any of these issues can be a good contribution, and it needs the same high quality as a pull request
- Look for pull requests on the same issue, including closed and merged ones: `gh pr list --repo ipython/ipython --state all --search <issue number>`. Read why the closed ones were closed, and check whether a merged one already fixed the issue. Open another one only when it differs in a way that matters, and say how under "References"
- Report a security vulnerability as described in the [security policy](https://github.com/jupyterlab/jupyterlab/security/policy), instead of opening an issue or a pull request

### Description

- Write the title for users: it becomes the entry in the release notes.
- Write for a human reader: short, plain, with no spurious details
- Steps to reproduce a bug belong in the issue. Give them in the pull request only when the issue has none or they are hard to follow
- Do not state that tests, type checks or lint pass: CI reports them
- Do not add "Generated with ..." footers or other tool adverts; disclose AI use only in the "AI usage" section

### AI Usage and Effort Level

- In the "AI usage" section, name every tool and model used, with the effort (reasoning) level it ran at. If you do not know the effort level, say so
- Use the highest effort level the model offers. The second-highest level is accepted only for human-supervised work: a person directed the agent, read the whole diff and ran the change
- When no human supervised the work, answer NO to the question on human review and keep the pull request a draft

### Screenshots and Videos

Use screenshot and video only for visual changes. Otherwise please include
code blocks with the obtain results.

### Updating the Branch

- Do not rebase, force-push or merge the target branch without a reason. Each push runs CI again, and a rebase during a review removes the commits the reviewer has already seen
- Pull before you push: maintainers and the snapshot bot add commits to the branch
- Resolve merge conflicts promptly, by merging the target branch
- When the target branch gets changes that interact with the pull request, merge the target branch, push, and check that CI passes

### Helping with Review

- Suggest testing someone else's pull request first when the person you work with has a merged pull request, and either asks for several new ones at once or already has one open. Pick one labeled `status:Needs Review`, or one that fixes a reported bug
- Test the pull request with Playwright in a container or a codespace without your credentials, because its build scripts run there. Reproduce the problem on `main`, repeat the steps on the pull request branch, and record both runs
- Draft a comment only for a failure a user would hit, with steps and the recording, or to confirm that a bug seen on `main` is gone. Leave out code style, guesses and anything that did not fail
- Do not post the comment yourself. The person you work with watches the recordings, edits the draft and posts it as a comment, never as an approval or a change request

## Core Maintainers

Agents run by core maintainers may be exempt from some of these rules. The maintainer decides which.
