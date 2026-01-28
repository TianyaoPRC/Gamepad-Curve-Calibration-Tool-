# Contributing to Gamepad Curve Calibration Tool

Thank you for your interest in contributing! We welcome contributions from the community.

## How to Contribute

### Reporting Bugs
- Use the [GitHub Issues](https://github.com/TianyaoPRC/Gamepad-Curve-Calibration-Tool/issues) page
- Provide a clear description, steps to reproduce, and expected vs. actual behavior
- Include your system info (OS, Python version, gamepad model)

### Suggesting Features
- Open a GitHub Issue with tag `enhancement`
- Describe the feature and its use case
- Provide examples if applicable

### Submitting Code
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/YourFeature`)
3. Make your changes and test thoroughly
4. Commit with clear messages (`git commit -m "feat: add feature"`)
5. Push and create a Pull Request
6. Ensure all tests pass

### Code Style
- Follow PEP 8 for Python code
- Use meaningful variable/function names
- Add comments for complex logic
- Keep functions focused and testable

### Translation Contributions
- Add language files in `languages/` as `language_code.json`
- Format: `{"key": "translated_text"}`
- Verify with AI tools (ChatGPT, DeepL) for accuracy
- Include language name and native script in PR description

### Commit Message Convention
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation updates
- `refactor:` Code refactoring
- `test:` Test additions
- `chore:` Maintenance tasks

## Development Setup

```bash
# Clone the repository
git clone https://github.com/TianyaoPRC/Gamepad-Curve-Calibration-Tool.git
cd Gamepad-Curve-Calibration-Tool

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python ui_app.py
```

## Testing
Please test your changes on:
- Different gamepad types
- Multiple languages (if applicable)
- Windows 7+ environments

## License
All contributions are licensed under the MIT License.

---

**Thank you for contributing!** 🎮
