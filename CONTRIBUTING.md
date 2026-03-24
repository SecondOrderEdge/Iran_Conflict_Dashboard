# Contributing to Iran Conflict Escalation Dashboard

Thank you for your interest in contributing. This document covers how to propose changes, submit pull requests, and maintain code quality.

---

## Getting Started

1. **Fork** the repository and clone your fork locally.

   ```bash
   git clone https://github.com/<your-username>/Iran_Conflict_Dashboard.git
   cd Iran_Conflict_Dashboard
   ```

2. **Create a branch** for your change. Use a descriptive name:

   ```bash
   git checkout -b feature/add-shipping-rate-signal
   # or
   git checkout -b fix/gdelt-timeout-handling
   ```

3. **Install dependencies** in a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Make your changes**, then commit with a clear message:

   ```bash
   git add .
   git commit -m "feat: add Baltic Dry Index as proxy shipping signal"
   ```

5. **Push** to your fork and open a **Pull Request** against the `main` branch.

---

## Areas for Contribution

The following areas are actively sought:

| Area | Description |
|---|---|
| **New data sources** | Shipping rates (BDI), satellite AIS data, social media sentiment |
| **Alternative signals** | Options market implied volatility term structure, CDS spreads |
| **Model improvements** | Backtesting against historical escalation events (2019 Abqaiq attack, 2020 Soleimani strike) |
| **OSINT database** | Expanding or curating the OSINT attack-wave database used for ground-truth model training |
| **ICEI calibration** | Tuning ICEI component budgets or bootstrap parameters (`N_BOOTSTRAP`, confidence interval methodology) |
| **Weight optimization** | Alternative approaches to `ENABLE_WEIGHT_OPTIMIZATION` (e.g., regularized regression, time-decayed weighting) |
| **Additional tickers** | Emerging market ETFs, airline/shipping equities |
| **Automation** | GitHub Actions workflow for scheduled daily runs |
| **Tests** | Unit tests for `build_signal_table()`, `add_escalation_probabilities()`, `get_weights()`, etc. |
| **Documentation** | Methodology explanations, signal justifications, worked examples |

---

## Code Style

- Keep changes to the notebook **sectioned and annotated** — each major section should have a markdown header explaining what it does.
- Use descriptive variable names; avoid single-letter abbreviations outside tight numerical loops.
- New signals should follow the existing normalization pipeline: raw → z-score → clip → normalize to `[-1, +1]`.
- If adding a new weighted signal, update the `get_weights()` function and ensure all weights still sum to 1.0. If `ENABLE_WEIGHT_OPTIMIZATION = True`, empirical weights are derived at runtime via logistic regression — verify your new signal does not break this path.
- OSINT-sourced signals must pull from the public OSINT database (or a configurable URL) and never embed raw event data in the notebook.
- Do not hard-code credentials. Always read from environment variables.

---

## Pull Request Checklist

Before submitting a PR, please confirm:

- [ ] Changes are limited to the scope described in the PR
- [ ] New signals are documented in the PR description (source, rationale, weight)
- [ ] No credentials, API keys, or personal data are included
- [ ] No large binary files are committed (PDFs, PNGs, CSVs)
- [ ] The notebook still runs cleanly top-to-bottom in Google Colab
- [ ] If modifying the OSINT layer, `ENABLE_OSINT = False` still produces a valid (reduced) model run

---

## Reporting Issues

If you find a bug or have a feature request, please open a [GitHub Issue](https://github.com/SecondOrderEdge/Iran_Conflict_Dashboard/issues) and include:

- A description of the problem or request
- Steps to reproduce (for bugs)
- Python version and environment (local vs. Colab)
- Relevant error messages or tracebacks

---

## Code of Conduct

Be respectful and constructive. This repository covers a sensitive geopolitical topic. Contributions should remain analytically focused and avoid political advocacy. All discussion should center on improving the methodology, data quality, and code — not on expressing political opinions about the conflict itself.

---

## License

By contributing, you agree that your contributions will be licensed under the same [MIT License](./LICENSE) that covers this project.
