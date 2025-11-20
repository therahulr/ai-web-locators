# AI-Assisted Locator Generation & Test Documentation Tool

An intelligent Python-based tool that assists QA engineers in pre-automation activities by automatically generating locators, documenting test steps, and analyzing web applications using AI vision and DOM analysis.

## Features

- **AI-Powered Element Analysis**: Uses OpenAI GPT-4o to intelligently identify interactive elements
- **Smart Locator Generation**: Generates pythonic locators with priority (ID > XPath > CSS)
- **Real-time Validation**: Validates locators on live pages with retry mechanism
- **Auto Documentation**: Creates markdown documentation of user actions and test steps
- **Interactive CLI**: Support for multiple commands (capture, steps, ask, etc.)
- **Conversation Context**: Maintains context for follow-up queries
- **Clean Code Output**: Generates production-ready Python locator files

## Technology Stack

- **Python**: 3.9+
- **Browser Automation**: Playwright (primary), Selenium (fallback)
- **AI Model**: OpenAI GPT-4o (vision + text)
- **Storage**: JSON (session data), Python files (locators), Markdown (docs)

## Project Structure

```
ai-web-locators/
├── src/
│   ├── __init__.py
│   ├── main.py                    # Entry point & CLI
│   ├── browser_manager.py         # Playwright/Selenium wrapper
│   ├── dom_analyzer.py            # DOM extraction & processing
│   ├── ai_engine.py               # OpenAI API integration
│   ├── locator_generator.py       # Locator creation & validation
│   ├── file_manager.py            # File I/O operations
│   ├── conversation_manager.py    # AI context & history
│   └── utils.py                   # Helpers & utilities
├── config/
│   └── config.yaml                # Configuration
├── output/
│   ├── locators/                  # Generated locator files
│   ├── docs/                      # Markdown documentation
│   └── sessions/                  # Session snapshots
├── logs/
│   └── app.log
├── requirements.txt
└── README.md
```

## Installation

### Prerequisites

- Python 3.9 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai-web-locators
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv

   # Activate on Linux/Mac
   source venv/bin/activate

   # Activate on Windows
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers**
   ```bash
   playwright install chromium
   ```

5. **Set up environment variables**
   ```bash
   # Copy example file
   cp .env.example .env

   # Edit .env and add your OpenAI API key
   # OPENAI_API_KEY=sk-...
   ```

6. **Export environment variable**
   ```bash
   # Linux/Mac
   export OPENAI_API_KEY='your-api-key-here'

   # Windows
   set OPENAI_API_KEY=your-api-key-here
   ```

## Usage

### Starting the Tool

```bash
python src/main.py
```

This will:
1. Launch Chrome browser
2. Start interactive CLI
3. Wait for your commands

### Available Commands

| Command | Description |
|---------|-------------|
| `capture` | Analyze current page and generate locators |
| `steps` | Generate test steps for current workflow |
| `elements` | List all identified elements on current page |
| `sections` | Identify page sections/modules |
| `retry` | Re-analyze current page with fresh AI request |
| `ask <query>` | Ask natural language question about current page |
| `save` | Save locators to Python file |
| `docs` | Export documentation to markdown |
| `status` | Show current session statistics |
| `list` | List generated files |
| `clear` | Clear conversation history |
| `exit` / `quit` | Exit tool |

### Typical Workflow

1. **Start the tool**
   ```bash
   python src/main.py
   ```

2. **Navigate manually** in the browser to your application

3. **Capture page elements**
   ```
   > capture
   ```
   This will:
   - Take screenshot
   - Extract DOM
   - Analyze with AI
   - Generate locators
   - Validate on live page

4. **Ask follow-up questions**
   ```
   > ask What is the locator for the login button?
   > ask How can I select items from the dropdown?
   ```

5. **Generate test steps**
   ```
   > steps
   ```

6. **Save locators to file**
   ```
   > save
   ```
   Generates: `output/locators/page_name_locators.py`

7. **Export documentation**
   ```
   > docs
   ```
   Generates: `output/docs/session_timestamp.md`

## Example Output

### Generated Locator File

```python
"""
Locator file for LoginPageLocators
Generated: 2025-11-20 14:30:00
"""

from typing import Tuple


class LoginPageLocators:
    """Page locators"""

    # Static Locators
    USERNAME_INPUT = ('id', "username")
    PASSWORD_INPUT = ('xpath', "//input[@type='password']")
    LOGIN_BUTTON = ('css', "button[type='submit']")
    FORGOT_PASSWORD_LINK = ('xpath', "//a[contains(text(), 'Forgot Password')]")
    REMEMBER_ME_CHECKBOX = ('id', "remember")

    # Dynamic Locators
    @staticmethod
    def error_message_by_field(field_name: str) -> Tuple[str, str]:
        """Get error message for specific field"""
        return ('xpath', f"//div[@data-field='{field_name}']//span[@class='error']")
```

### Generated Documentation

```markdown
# Test Session Documentation

**Session ID:** 20251120_143000
**Started:** 2025-11-20T14:30:00
**Pages Visited:** 3
**Locators Generated:** 15

---

## Pages Visited

### 1. Login Page
**URL:** https://example.com/login
**Timestamp:** 2025-11-20T14:30:15

### 2. Dashboard
**URL:** https://example.com/dashboard
**Timestamp:** 2025-11-20T14:32:45

## Locators Generated

### login_page
- USERNAME_INPUT
- PASSWORD_INPUT
- LOGIN_BUTTON
- FORGOT_PASSWORD_LINK
- REMEMBER_ME_CHECKBOX

### dashboard
- NEW_APPLICATION_BUTTON
- SEARCH_INPUT
- FILTER_DROPDOWN
```

## Configuration

Edit `config/config.yaml` to customize:

```yaml
openai:
  model: "gpt-4o"              # AI model to use
  max_tokens: 4000
  temperature: 0.3

browser:
  headless: false              # Set true for no browser window
  window_size: [1920, 1080]
  timeout: 30000

locator:
  priority: ["id", "xpath", "css"]
  retry_attempts: 3
  validation_timeout: 5000

logging:
  level: "INFO"                # DEBUG, INFO, WARNING, ERROR
```

## Naming Conventions

The tool follows these locator naming conventions:

- **Format**: `ALL_CAPS_SNAKE_CASE`
- **Descriptive**: `NEW_APPLICATION_LINK` not `LINK_1`
- **Element Type Suffix**: `_BUTTON`, `_INPUT`, `_LINK`, `_CHECKBOX`, `_DROPDOWN`

Examples:
- ✅ `USERNAME_INPUT`
- ✅ `LOGIN_BUTTON`
- ✅ `FORGOT_PASSWORD_LINK`
- ✅ `COUNTRY_DROPDOWN`
- ❌ `input1`
- ❌ `btn_submit`
- ❌ `link`

## Advanced Features

### Context-Aware Conversations

The tool maintains conversation context, allowing natural follow-ups:

```
> capture
[AI analyzes page and generates locators]

> ask What was the XPath for the submit button?
[AI answers based on previous analysis]

> ask Can you suggest a better locator for the email field?
[AI provides recommendations]
```

### Dynamic Locators

For repeated elements (lists, tables), the tool generates parameterized methods:

```python
@staticmethod
def checkbox_by_label(label: str) -> Tuple[str, str]:
    """Checkbox by label text"""
    return ('xpath', f"//input[@type='checkbox' and following-sibling::label[text()='{label}']]")

@staticmethod
def table_cell_by_row_and_col(row: int, col: int) -> Tuple[str, str]:
    """Table cell by row and column"""
    return ('xpath', f"//table//tr[{row}]/td[{col}]")
```

## Troubleshooting

### Browser doesn't launch
- Ensure Playwright is installed: `playwright install chromium`
- Check config: `browser.headless` should be `false` for visible browser

### OpenAI API errors
- Verify API key is set: `echo $OPENAI_API_KEY`
- Check API quota at https://platform.openai.com/usage
- Ensure valid model in config: `gpt-4o` or `gpt-4o-mini`

### Validation failures
- Increase timeout in config: `locator.validation_timeout`
- Use `retry` command to re-analyze with AI
- Check if page is fully loaded before running `capture`

### DOM too large
- Tool auto-truncates DOM to 50KB for AI processing
- Interactive elements are still extracted correctly

## Performance Tips

1. **Reduce API costs**: Use `gpt-4o-mini` for simpler pages
2. **Faster analysis**: Set `browser.headless: true` if you don't need to see the browser
3. **Better results**: Wait for page to fully load before `capture`
4. **Accurate locators**: Add `data-testid` attributes to your application

## Logging

Logs are saved to `logs/app.log` with rotation:
- Max file size: 10MB
- Backup count: 5 files
- Levels: DEBUG, INFO, WARNING, ERROR

View logs:
```bash
tail -f logs/app.log
```

## Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black src/
```

### Linting
```bash
pylint src/
```

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or feature requests, please open an issue on GitHub.

## Changelog

### v1.0.0 (2025-11-20)
- Initial release
- AI-powered locator generation
- Real-time validation
- Interactive CLI
- Markdown documentation
- Conversation context

## Roadmap

Future enhancements (planned):
- [ ] Mobile app support (Appium integration)
- [ ] Auto-generate Page Object Model classes
- [ ] Visual regression testing
- [ ] Multi-language locator export (Java/C#)
- [ ] CI/CD integration
- [ ] Web UI dashboard
