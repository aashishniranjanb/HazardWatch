# Contributing to HazardWatch

Thank you for your interest in contributing to **HazardWatch**! We welcome bug reports, documentation enhancements, feature proposals, and code contributions.

---

## Code of Conduct

All contributors and maintainers are expected to uphold a respectful, inclusive, and professional environment. Please treat all community members with courtesy.

---

## How to Contribute

### 1. Reporting Bugs
- Search existing GitHub Issues before opening a new ticket.
- Use the **Bug Report** issue template.
- Include OS version, Python version, Node.js version, and ESP32 COM port hardware details.
- Provide logs from `backend_stderr.log` or serial output where applicable.

### 2. Proposing Features
- Open a feature request ticket describing the problem, proposed solution, and industrial safety considerations.
- Discuss design with maintainers before opening large pull requests.

### 3. Submitting Pull Requests
1. Fork the repository.
2. Create a dedicated topic branch: `git checkout -b feature/my-new-feature`.
3. Adhere to existing coding style:
   - **Backend:** PEP 8 compliance, typed functions, docstrings.
   - **Frontend:** TypeScript strict types, Tailwind CSS utility conventions.
   - **Firmware:** Explicit pin definitions, fail-safe interlocks, standard C++.
4. Ensure all unit and regression tests pass:
   ```powershell
   $env:PYTHONPATH = "backend;" + $env:PYTHONPATH
   python -m unittest discover -s tests -p "test_*.py"
   ```
5. Ensure frontend builds cleanly:
   ```bash
   cd frontend
   npm run build
   ```
6. Commit changes with clear, descriptive commit messages.
7. Submit the pull request referencing any relevant issue numbers.

---

## Safety & Scientific Integrity Policy

HazardWatch is an experimental monitoring research system:
- **Never bypass actuator safety locks:** Firmware relay control must default to safe-OFF (`HIGH` on active-LOW relays).
- **Never synthesize live data:** Missing sensor channels must evaluate to `null` (`None`), never `0` or interpolated values.
- **Accurate claims:** Clearly differentiate between synthetic benchmark evaluations and genuine physical sensor validations.
