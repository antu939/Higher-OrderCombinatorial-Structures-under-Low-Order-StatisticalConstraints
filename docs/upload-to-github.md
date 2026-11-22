# Publishing the repository to GitHub

The repository is already laid out for a public release. Before pushing:

1. Review `paper/` and confirm that the manuscript may be redistributed.
2. Fill the empty `CITATION.cff` and `LICENSE` placeholders with the real
   author(s), copyright holder, and license.
3. Optionally replace `<YOUR_REPOSITORY_URL>` in `README.md`.
4. Run the release checks from the repository root:

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python -m examples.run_all --output results-local
python tests/check_outputs.py results-local
python tests/verify_paper_numbers.py
```

5. Create an empty GitHub repository (without an additional README or
   `.gitignore`), replace `<YOUR_USERNAME>` and `<YOUR_REPO>`, and push:

```bash
git init
git add .
git commit -m "Initial reproducible research release"
git branch -M main
git remote add origin https://github.com/<YOUR_USERNAME>/<YOUR_REPO>.git
git push -u origin main
```

You can also upload through the GitHub web UI; preserve the directory
structure, including `.github/workflows/` and `.gitignore`.

## Release checklist

- [ ] `CITATION.cff` filled with real author / affiliation / preferred citation
- [ ] `LICENSE` filled with the chosen license and copyright holder
- [ ] `references.bib` contains only verified works (currently empty by design)
- [ ] `paper/main-zh.pdf` compiled locally (currently an empty placeholder)
- [ ] `paper/main-en.pdf` matches `paper/main-en.tex`
- [ ] All 26 unit tests pass
- [ ] `tests/check_outputs.py` validates the six experiment outputs
- [ ] `tests/verify_paper_numbers.py` verifies every number in the papers
- [ ] No personal data, tokens, unapproved datasets, or sensitive files
- [ ] `.DS_Store`, LaTeX build artifacts, and `results-local/` are ignored
