# Branching and Release Workflow

This document defines the recommended Git workflow for the `psychchart` project.

The goal is to keep `main` stable, make ongoing development safer, and avoid the accumulation of old experimental branches. The workflow is intentionally simple and suitable for a small scientific/open-source project that is evolving quickly but still needs reliable releases.

---

## 1. Branch roles

The project should use two long-lived branches:

```text
main
```

and:

```text
develop
```

All other branches should be temporary and should be deleted after their Pull Requests are merged or closed.

---

## 2. The `main` branch

The `main` branch is the stable branch of the project.

It should represent the version of `psychchart` that is considered reliable enough for normal use. Code in `main` should be tested, documented when necessary, and suitable for tagging releases.

### Rules for `main`

Use `main` for:

- stable code;
- release candidates;
- tagged releases;
- emergency hotfixes;
- final integration from `develop`.

Avoid using `main` for:

- experimental work;
- incomplete features;
- large refactors under development;
- untested UI changes;
- exploratory YAML/API changes.

In practice, `main` should only receive changes through Pull Requests.

Recommended protection rules for `main` on GitHub:

- require Pull Request before merging;
- require tests to pass before merging;
- prevent direct pushes;
- require branches to be up to date before merging when possible;
- delete feature branches after merge.

---

## 3. The `develop` branch

The `develop` branch is the integration branch.

It is where new features, internal improvements, UI work, examples, documentation, and refactors are integrated before they are promoted to `main`.

### Rules for `develop`

Use `develop` for:

- integrating new feature branches;
- testing features together before release;
- preparing the next minor or patch release;
- accumulating non-emergency improvements.

Avoid using `develop` for:

- broken code that prevents normal testing;
- long-lived experimental work without a feature branch;
- releases without final validation on `main`.

A feature should normally follow this path:

```text
feature/...  →  develop  →  main
```

A bug fix should normally follow this path:

```text
fix/...  →  develop  →  main
```

A hotfix should normally follow this path:

```text
hotfix/...  →  main  →  develop
```

---

## 4. Creating the `develop` branch

When the repository is clean and `main` is up to date, create `develop` from `main`:

```bash
git checkout main
git pull origin main
git checkout -b develop
git push -u origin develop
```

After that, `develop` becomes the normal base branch for new features.

---

## 5. Starting a new feature

Always start new feature work from `develop`.

Example:

```bash
git checkout develop
git pull origin develop
git checkout -b feature/intervention-zone-presets
```

Make changes, then run tests:

```bash
pytest
```

If the feature affects the frontend:

```bash
cd frontend
npm ci
npm run build
```

If the feature affects rendering examples:

```bash
psychchart examples/some_example.yaml
```

Commit the changes:

```bash
git add .
git commit -m "feature: add intervention zone presets"
```

Push the branch:

```bash
git push -u origin feature/intervention-zone-presets
```

Open a Pull Request:

```text
base: develop
head: feature/intervention-zone-presets
```

After the PR is merged, delete the branch:

```bash
git branch -d feature/intervention-zone-presets
git push origin --delete feature/intervention-zone-presets
```

If Git says the local branch is not fully merged, verify that the PR was merged and then delete locally with:

```bash
git branch -D feature/intervention-zone-presets
```

---

## 6. Starting a bug fix

Bug fixes that are not urgent should also start from `develop`.

Example:

```bash
git checkout develop
git pull origin develop
git checkout -b fix/index-label-position
```

After making the correction:

```bash
pytest
psychchart examples/itu_field_labels.yaml
```

Commit and push:

```bash
git add .
git commit -m "fix: correct index field label placement"
git push -u origin fix/index-label-position
```

Open a Pull Request:

```text
base: develop
head: fix/index-label-position
```

---

## 7. Emergency hotfixes

Use a hotfix branch only when `main` has a serious problem that must be fixed immediately.

Hotfixes should branch from `main`, not from `develop`.

Example:

```bash
git checkout main
git pull origin main
git checkout -b hotfix/render-file-savefig
```

Apply the fix and test it:

```bash
pytest
psychchart examples/intervention_zones_minimal.yaml
```

Commit and push:

```bash
git add .
git commit -m "hotfix: fix savefig with intervention zone hatches"
git push -u origin hotfix/render-file-savefig
```

Open a Pull Request:

```text
base: main
head: hotfix/render-file-savefig
```

After the hotfix is merged into `main`, bring the fix back into `develop`:

```bash
git checkout develop
git pull origin develop
git merge origin/main
git push origin develop
```

This prevents `develop` from reintroducing the bug later.

---

## 8. Promoting `develop` to `main`

When `develop` is stable and ready for release, open a Pull Request:

```text
base: main
head: develop
```

Before opening or merging this PR, run a full validation locally:

```bash
git checkout develop
git pull origin develop
pytest
```

Validate relevant examples:

```bash
psychchart examples/minimal.yaml
psychchart examples/itu_field_labels.yaml
psychchart examples/index_zone_itu_labeled.yaml
psychchart examples/intervention_zones_minimal.yaml
psychchart examples/thermal_trajectory_classified.yaml
```

If the frontend changed:

```bash
cd frontend
npm ci
npm run build
```

If the API changed:

```bash
uvicorn psychchart.api.fastapi_app:app --reload
```

Then test in another terminal:

```bash
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/readout \
  -H 'Content-Type: application/json' \
  -d '{"T": 31.0, "RH_pct": 65.0, "pressure": 101325.0}'
```

Only merge `develop` into `main` after the validation is clean.

---

## 9. Release workflow

Releases should be created from `main` only.

### 9.1 Update `main`

```bash
git checkout main
git pull origin main
```

### 9.2 Confirm tests

```bash
pytest
```

### 9.3 Confirm package version

```bash
python -c "import importlib.metadata as m; print(m.version('psychchart'))"
```

### 9.4 Create a tag

Use annotated tags:

```bash
git tag -a v1.0.2 -m "Release v1.0.2"
git push origin v1.0.2
```

### 9.5 Verify that the tag points to `main`

Annotated tags point to a tag object, so use `^{}` to resolve the commit:

```bash
git rev-parse v1.0.2^{}
git rev-parse origin/main
```

Both hashes should match.

You can also inspect the tag:

```bash
git show --no-patch --format='%H %s' v1.0.2
```

---

## 10. Cleaning merged branches

After a PR is merged, delete the remote branch:

```bash
git push origin --delete feature/some-feature
```

Delete the local branch:

```bash
git branch -d feature/some-feature
```

If the branch was squash-merged, Git may not recognize it as merged. In that case, after confirming the PR is merged, use:

```bash
git branch -D feature/some-feature
```

Then prune stale remote references:

```bash
git fetch --prune
```

List remote branches:

```bash
git branch -r
```

A clean repository should normally show only:

```text
origin/HEAD -> origin/main
origin/main
origin/develop
```

Temporary feature branches should not remain indefinitely.

---

## 11. Naming conventions

Use descriptive branch names.

Recommended prefixes:

```text
feature/...
fix/...
hotfix/...
docs/...
refactor/...
test/...
release/...
```

Examples:

```text
feature/intervention-zone-presets
feature/frontend-projects-panel
fix/index-zone-label-placement
hotfix/savefig-hatches
refactor/data-layer-runtime
docs/branching-workflow
test/api-render-endpoints
```

Keep branch names short but specific.

---

## 12. Commit message conventions

Use short, explicit commit messages.

Recommended format:

```text
scope: action
```

Examples:

```text
config: expose intervention zones in app config
render: integrate intervention zones into chart pipeline
plot: avoid null hatches in intervention contour fills
test: cover labeled index zones
docs: add frontend development guide
frontend: add interactive workspace base layout
```

Good commit messages should explain what changed, not just that something changed.

Avoid vague messages such as:

```text
update
fix things
changes
more code
final version
```

---

## 13. Pull Request checklist

Every Pull Request should answer:

- What changed?
- Why was it necessary?
- Which files or modules were affected?
- How was it tested?
- Does it affect examples, documentation, API, CLI, or frontend?

A good PR body should include a validation block like:

```markdown
## Validation

```bash
pytest
psychchart examples/minimal.yaml
```
```

For frontend PRs:

```markdown
## Validation

```bash
cd frontend
npm ci
npm run build
VITE_PSYCHCHART_API_URL=http://127.0.0.1:8000 npm run dev
```
```

For API PRs:

```markdown
## Validation

```bash
uvicorn psychchart.api.fastapi_app:app --reload
curl http://127.0.0.1:8000/health
```
```

---

## 14. Recommended daily workflow

Start by updating your working branch:

```bash
git checkout develop
git pull origin develop
```

Create a focused branch:

```bash
git checkout -b feature/small-focused-change
```

Work in small commits.

Run tests before pushing:

```bash
pytest
```

Push and open a PR to `develop`:

```bash
git push -u origin feature/small-focused-change
```

After merge, clean local and remote branches.

---

## 15. What not to do

Avoid long-lived feature branches that diverge for many weeks.

Avoid mixing unrelated work in the same branch, for example:

```text
frontend redesign + data layer refactor + release bump + docs rewrite
```

Prefer smaller PRs:

```text
PR 1: add API endpoint
PR 2: wire frontend client
PR 3: add UI panel
PR 4: add documentation
PR 5: add release bump
```

This keeps reviews easier and reduces merge conflicts.

---

## 16. Recommended workflow for `psychchart`

For the current state of this project, the recommended workflow is:

```text
main
  ↑
  │ release PRs only
  │
develop
  ↑
  │ feature/fix/docs PRs
  │
feature/*, fix/*, docs/*, refactor/*
```

Use `develop` as the place where the next version is assembled.

Use `main` as the stable release branch.

Use short-lived feature branches for all actual work.

---

## 17. Minimal command reference

Create `develop`:

```bash
git checkout main
git pull origin main
git checkout -b develop
git push -u origin develop
```

Start a feature:

```bash
git checkout develop
git pull origin develop
git checkout -b feature/my-feature
```

Push a feature:

```bash
git push -u origin feature/my-feature
```

Merge feature through PR:

```text
feature/my-feature → develop
```

Promote develop to main:

```text
develop → main
```

Tag release from main:

```bash
git checkout main
git pull origin main
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin vX.Y.Z
```

Delete merged branch:

```bash
git push origin --delete feature/my-feature
git branch -d feature/my-feature
git fetch --prune
```

---

## 18. Final recommendation

Keep the workflow boring and predictable.

For `psychchart`, the safest pattern is:

1. develop new work in short-lived branches;
2. merge features into `develop`;
3. validate `develop` as a release candidate;
4. merge `develop` into `main` only when stable;
5. tag releases only from `main`;
6. delete old branches immediately after merge.

This keeps the repository clean, reduces risk, and makes the project easier to maintain as it grows.
