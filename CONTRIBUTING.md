# Contributing to Loam

Loam is open source under the [MIT License](LICENSE) — fork it, build on it, ship
your own worlds. Contributions back to this repository are welcome, with one
governing rule.

## Every check-in requires maintainer approval

- `main` is protected — no direct pushes.
- Propose changes as a pull request from a fork or branch.
- [`.github/CODEOWNERS`](.github/CODEOWNERS) routes every path to the maintainer
  (@nadeauglenn1-max), so with branch protection set to *require review from Code
  Owners*, approval is enforced by the repo, not just by convention.
- The maintainer has final say on what merges.

## How to contribute

1. Fork (or branch) and make your change.
2. Keep the suite green and the bar high: `pytest --cov=loam --cov-fail-under=90`.
3. Docs move with the code — update the README/docs in the *same* PR that changes
   behavior.
4. Open a focused PR describing the change. Small, single-purpose PRs merge
   fastest.

By contributing, you agree that your contribution is provided under the project's
MIT License.
