"""
Main CLI Module
Interactive command-line interface for AI-Assisted Locator Generation Tool
"""

import sys
import os
import logging
from pathlib import Path
from typing import Optional
import yaml

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.browser_manager import BrowserManager
from src.dom_analyzer import DOMAnalyzer
from src.ai_engine import AIEngine
from src.locator_generator import LocatorGenerator
from src.file_manager import FileManager
from src.conversation_manager import ConversationManager
from src import utils
from src.utils import (
    print_success, print_error, print_warning, print_info, print_header,
    sanitize_filename, extract_page_name_from_url
)

logger = logging.getLogger(__name__)


class LocatorTool:
    """Main application class"""

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize the tool

        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self._setup_logging()

        # Get OpenAI API key
        api_key_env = self.config['openai'].get('api_key_env', 'OPENAI_API_KEY')
        api_key = os.getenv(api_key_env)

        if not api_key:
            raise ValueError(f"OpenAI API key not found. Set {api_key_env} environment variable.")

        self.config['openai']['api_key'] = api_key

        # Initialize components
        self.browser = BrowserManager(self.config['browser'])
        self.dom_analyzer = DOMAnalyzer()
        self.ai_engine = AIEngine(self.config['openai'])
        self.locator_gen = LocatorGenerator(self.browser, self.config['locator'])
        self.file_manager = FileManager(self.config['output'])
        self.conversation = ConversationManager()

        self.running = False
        self.current_page_name: Optional[str] = None

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                raise FileNotFoundError(f"Config file not found: {config_path}")

            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)

            utils.validate_config(config)
            return config

        except Exception as e:
            print_error(f"Failed to load config: {e}")
            sys.exit(1)

    def _setup_logging(self) -> None:
        """Setup logging configuration"""
        log_config = self.config['logging']
        utils.setup_logging(
            log_file=log_config['file'],
            log_level=log_config['level'],
            max_bytes=log_config.get('max_bytes', 10485760),
            backup_count=log_config.get('backup_count', 5)
        )

    def start(self) -> None:
        """Start the tool"""
        try:
            print_header("AI-Assisted Locator Generation Tool v1.0")
            print_info("Initializing browser...")

            self.browser.launch()
            self.running = True

            print_success("Browser launched successfully!")
            print_info("Navigate to your application manually, then type commands.")
            print_info("Type 'help' for available commands.\n")

            self._command_loop()

        except KeyboardInterrupt:
            print_info("\nShutting down...")
        except Exception as e:
            print_error(f"Failed to start: {e}")
            logger.exception("Startup error")
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop the tool and cleanup"""
        if self.running:
            print_info("Saving session...")
            self._save_session()

            print_info("Closing browser...")
            self.browser.close()

            self.running = False
            print_success("Tool stopped successfully")

    def _command_loop(self) -> None:
        """Main command loop"""
        while self.running:
            try:
                command = input(f"{utils.Colors.BOLD}> {utils.Colors.ENDC}").strip()

                if not command:
                    continue

                self._execute_command(command)

            except KeyboardInterrupt:
                print()
                if self._confirm("Exit tool?"):
                    break
            except Exception as e:
                print_error(f"Command failed: {e}")
                logger.exception("Command execution error")

    def _execute_command(self, command: str) -> None:
        """
        Execute user command

        Args:
            command: Command string
        """
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        commands = {
            'help': self._cmd_help,
            'capture': self._cmd_capture,
            'steps': self._cmd_steps,
            'elements': self._cmd_elements,
            'sections': self._cmd_sections,
            'retry': self._cmd_retry,
            'ask': lambda: self._cmd_ask(args),
            'save': self._cmd_save,
            'docs': self._cmd_docs,
            'status': self._cmd_status,
            'list': self._cmd_list,
            'clear': self._cmd_clear,
            'exit': self._cmd_exit,
            'quit': self._cmd_exit
        }

        if cmd in commands:
            commands[cmd]()
        else:
            print_warning(f"Unknown command: {cmd}. Type 'help' for available commands.")

    def _cmd_help(self) -> None:
        """Display help information"""
        help_text = """
Available Commands:

  capture      - Analyze current page and generate locators
  steps        - Generate test steps for current workflow
  elements     - List all identified elements on current page
  sections     - Identify page sections/modules
  retry        - Re-analyze current page with fresh AI request
  ask <query>  - Ask natural language question about current page
  save         - Save locators to Python file
  docs         - Export documentation to markdown
  status       - Show current session statistics
  list         - List generated files
  clear        - Clear conversation history
  exit/quit    - Exit tool

Navigation:
  Navigate manually in the browser window before running commands.
"""
        print(help_text)

    def _cmd_capture(self) -> None:
        """Capture and analyze current page"""
        try:
            print_info("Capturing current page...")

            # Update page info
            self.browser.update_page_info()
            url = self.browser.current_url
            title = self.browser.current_title

            print_info(f"Page: {title}")
            print_info(f"URL: {url}")

            # Capture screenshot
            print_info("Taking screenshot...")
            screenshot_b64 = self.browser.capture_screenshot()

            # Extract DOM
            print_info("Extracting DOM...")
            raw_html = self.browser.get_dom()
            self.dom_analyzer.load_html(raw_html)
            cleaned_html = self.dom_analyzer.clean_html()
            sanitized_html = self.dom_analyzer.sanitize_for_ai(cleaned_html)

            # Get conversation context
            context = self.conversation.get_context_summary()

            # AI analysis
            print_info("Analyzing with AI (this may take 10-20 seconds)...")
            result = self.ai_engine.analyze_page(
                screenshot_b64,
                sanitized_html,
                url,
                context
            )

            # Process results
            elements = result.get('elements', [])
            dynamic_locators = result.get('dynamic_locators', [])

            print_success(f"Found {len(elements)} elements")

            if not elements:
                print_warning("No elements identified. Try retry or ask for specific elements.")
                return

            # Validate locators
            print_info("Validating locators...")
            validation_results = self.locator_gen.validate_batch(elements)

            # Display results
            print_header("Validation Results:")
            for result in validation_results:
                formatted = utils.format_validation_result(result)
                print(formatted)

            # Store valid locators
            self.current_page_name = extract_page_name_from_url(url)
            valid_locators = []

            for elem, val_result in zip(elements, validation_results):
                if val_result['valid']:
                    self.locator_gen.add_locator(
                        self.current_page_name,
                        elem['name'],
                        elem['locator_type'],
                        elem['locator_value']
                    )
                    valid_locators.append(elem['name'])

            # Store dynamic locators
            for dloc in dynamic_locators:
                self.locator_gen.add_dynamic_locator(self.current_page_name, dloc)

            # Update conversation
            self.conversation.add_page_visit(url, title)
            self.conversation.add_locators(self.current_page_name, valid_locators)
            self.conversation.add_interaction('capture', {'url': url}, result)

            # Summary
            summary = self.locator_gen.get_validation_summary()
            print_success(
                f"\nSummary: {summary['valid']}/{summary['total']} locators valid "
                f"({summary['success_rate']:.1f}% success rate)"
            )

            print_info(f"\nUse 'save' to export locators to Python file")

        except Exception as e:
            print_error(f"Capture failed: {e}")
            logger.exception("Capture error")

    def _cmd_steps(self) -> None:
        """Generate test steps"""
        try:
            print_info("Generating test steps...")

            # Capture current state
            self.browser.update_page_info()
            url = self.browser.current_url
            screenshot_b64 = self.browser.capture_screenshot()
            raw_html = self.browser.get_dom()
            self.dom_analyzer.load_html(raw_html)
            cleaned_html = self.dom_analyzer.clean_html()
            sanitized_html = self.dom_analyzer.sanitize_for_ai(cleaned_html)

            context = self.conversation.get_context_summary()

            print_info("AI is generating steps...")
            result = self.ai_engine.generate_test_steps(
                screenshot_b64,
                sanitized_html,
                url,
                context
            )

            # Display steps
            print_header(f"Test Steps: {result.get('title', 'Workflow')}")

            steps = result.get('steps', [])
            for step in steps:
                print(f"\n{step['step_number']}. {step['action']}")
                if step.get('locator') and step['locator'] != 'N/A':
                    print(f"   Locator: {step['locator']}")
                if step.get('description'):
                    print(f"   {step['description']}")

            if result.get('prerequisites'):
                print_header("Prerequisites:")
                for prereq in result['prerequisites']:
                    print(f"  • {prereq}")

            if result.get('validations'):
                print_header("Validations:")
                for validation in result['validations']:
                    print(f"  • {validation}")

            self.conversation.add_interaction('steps', {'url': url}, result)
            print_success("\nUse 'docs' to export to markdown")

        except Exception as e:
            print_error(f"Step generation failed: {e}")
            logger.exception("Steps error")

    def _cmd_elements(self) -> None:
        """List all elements on current page"""
        try:
            print_info("Extracting interactive elements...")

            raw_html = self.browser.get_dom()
            self.dom_analyzer.load_html(raw_html)
            elements = self.dom_analyzer.extract_interactive_elements()

            print_header(f"Found {len(elements)} Interactive Elements:")

            for idx, elem in enumerate(elements[:50], 1):  # Limit to 50
                elem_id = elem.get('id', 'N/A')
                elem_type = elem.get('type', 'unknown')
                elem_text = utils.truncate_text(elem.get('text', ''), 40)

                print(f"{idx}. {elem_type.upper()}")
                if elem_id != 'N/A':
                    print(f"   ID: {elem_id}")
                if elem_text:
                    print(f"   Text: {elem_text}")

            if len(elements) > 50:
                print_info(f"\n... and {len(elements) - 50} more elements")

        except Exception as e:
            print_error(f"Element extraction failed: {e}")
            logger.exception("Elements error")

    def _cmd_sections(self) -> None:
        """Identify page sections"""
        try:
            print_info("Identifying page sections...")

            screenshot_b64 = self.browser.capture_screenshot()
            raw_html = self.browser.get_dom()
            self.dom_analyzer.load_html(raw_html)
            cleaned_html = self.dom_analyzer.clean_html()

            sections = self.ai_engine.identify_page_sections(screenshot_b64, cleaned_html)

            print_header("Page Sections:")
            for idx, section in enumerate(sections, 1):
                print(f"{idx}. {section}")

            # Also show structure
            structure = self.dom_analyzer.get_page_structure()
            print_header("\nPage Structure:")
            print(f"  Header: {'Yes' if structure['has_header'] else 'No'}")
            print(f"  Navigation: {'Yes' if structure['has_nav'] else 'No'}")
            print(f"  Main Content: {'Yes' if structure['has_main'] else 'No'}")
            print(f"  Footer: {'Yes' if structure['has_footer'] else 'No'}")
            print(f"  Forms: {structure['forms_count']}")
            print(f"  Buttons: {structure['buttons_count']}")
            print(f"  Links: {structure['links_count']}")

        except Exception as e:
            print_error(f"Section identification failed: {e}")
            logger.exception("Sections error")

    def _cmd_retry(self) -> None:
        """Retry analysis with fresh request"""
        print_info("Retrying analysis...")
        self._cmd_capture()

    def _cmd_ask(self, question: str) -> None:
        """
        Ask question about current page

        Args:
            question: User question
        """
        try:
            if not question:
                question = input("Ask a question: ").strip()

            if not question:
                print_warning("No question provided")
                return

            print_info(f"Question: {question}")
            print_info("AI is thinking...")

            # Capture current state
            self.browser.update_page_info()
            url = self.browser.current_url
            screenshot_b64 = self.browser.capture_screenshot()
            raw_html = self.browser.get_dom()
            self.dom_analyzer.load_html(raw_html)
            cleaned_html = self.dom_analyzer.clean_html()
            sanitized_html = self.dom_analyzer.sanitize_for_ai(cleaned_html)

            context = self.conversation.get_context_summary()

            answer = self.ai_engine.answer_question(
                question,
                screenshot_b64,
                sanitized_html,
                url,
                context
            )

            print_header("Answer:")
            print(answer)

            self.conversation.add_question(question, answer)

        except Exception as e:
            print_error(f"Question failed: {e}")
            logger.exception("Ask error")

    def _cmd_save(self) -> None:
        """Save locators to Python file"""
        try:
            if not self.current_page_name:
                print_warning("No page analyzed yet. Run 'capture' first.")
                return

            if not self.locator_gen.locators.get(self.current_page_name):
                print_warning("No valid locators to save.")
                return

            filename = sanitize_filename(self.current_page_name) + "_locators.py"
            output_path = Path(self.config['output']['locators_dir']) / filename

            print_info(f"Saving locators to: {output_path}")

            self.locator_gen.generate_python_file(self.current_page_name, output_path)

            print_success(f"Locators saved successfully!")
            print_info(f"File: {output_path}")

        except Exception as e:
            print_error(f"Save failed: {e}")
            logger.exception("Save error")

    def _cmd_docs(self) -> None:
        """Export documentation"""
        try:
            stats = self.conversation.get_statistics()

            if stats['pages_visited'] == 0:
                print_warning("No pages visited yet.")
                return

            print_info("Generating documentation...")

            # Generate markdown content
            session_data = self.conversation.get_session_data()

            doc_lines = [
                f"# Test Session Documentation",
                f"\n**Session ID:** {stats['session_id']}",
                f"**Started:** {stats['started_at']}",
                f"**Pages Visited:** {stats['pages_visited']}",
                f"**Locators Generated:** {stats['total_locators']}",
                f"\n---\n",
                f"\n## Pages Visited\n"
            ]

            for idx, page in enumerate(session_data['pages_visited'], 1):
                doc_lines.append(f"\n### {idx}. {page['title']}")
                doc_lines.append(f"**URL:** {page['url']}")
                doc_lines.append(f"**Timestamp:** {page['timestamp']}\n")

            if session_data['locators_generated']:
                doc_lines.append(f"\n## Locators Generated\n")
                for loc_group in session_data['locators_generated']:
                    doc_lines.append(f"\n### {loc_group['page']}")
                    for locator in loc_group['locators']:
                        doc_lines.append(f"- {locator}")

            if session_data['questions_asked']:
                doc_lines.append(f"\n## Questions & Answers\n")
                for qa in session_data['questions_asked']:
                    doc_lines.append(f"\n**Q:** {qa['question']}")
                    doc_lines.append(f"\n**A:** {qa['answer']}\n")
                    doc_lines.append("---\n")

            doc_content = "\n".join(doc_lines)

            # Save to file
            filename = f"session_{stats['session_id']}.md"
            doc_path = self.file_manager.save_markdown_doc(doc_content, filename)

            print_success(f"Documentation exported!")
            print_info(f"File: {doc_path}")

        except Exception as e:
            print_error(f"Documentation export failed: {e}")
            logger.exception("Docs error")

    def _cmd_status(self) -> None:
        """Show session statistics"""
        stats = self.conversation.get_statistics()

        print_header("Session Status")
        print(f"Session ID: {stats['session_id']}")
        print(f"Started: {stats['started_at']}")
        print(f"Pages Visited: {stats['pages_visited']}")
        print(f"Locators Generated: {stats['total_locators']}")
        print(f"Questions Asked: {stats['questions_asked']}")
        print(f"Total Interactions: {stats['interactions']}")

        if self.current_page_name:
            print(f"\nCurrent Page: {self.current_page_name}")
            print(f"Current URL: {self.browser.current_url}")

        validation_summary = self.locator_gen.get_validation_summary()
        if validation_summary['total'] > 0:
            print(f"\nValidation Success Rate: {validation_summary['success_rate']:.1f}%")

    def _cmd_list(self) -> None:
        """List generated files"""
        print_header("Generated Files")

        locator_files = self.file_manager.list_locator_files()
        if locator_files:
            print("\nLocator Files:")
            for f in locator_files:
                print(f"  • {f}")
        else:
            print("\nNo locator files yet.")

        doc_files = self.file_manager.list_docs()
        if doc_files:
            print("\nDocumentation Files:")
            for f in doc_files:
                print(f"  • {f}")
        else:
            print("\nNo documentation files yet.")

    def _cmd_clear(self) -> None:
        """Clear conversation history"""
        if self._confirm("Clear conversation history?"):
            self.conversation.clear_history()
            print_success("History cleared")

    def _cmd_exit(self) -> None:
        """Exit the tool"""
        if self._confirm("Save session and exit?"):
            self.running = False

    def _save_session(self) -> None:
        """Save current session"""
        try:
            session_data = {
                'conversation': self.conversation.get_session_data(),
                'validation_results': self.locator_gen.validation_results,
                'statistics': self.conversation.get_statistics()
            }

            self.file_manager.save_session(session_data)
            logger.info("Session saved")

        except Exception as e:
            logger.error(f"Failed to save session: {e}")

    def _confirm(self, message: str) -> bool:
        """
        Ask for user confirmation

        Args:
            message: Confirmation message

        Returns:
            True if confirmed
        """
        response = input(f"{message} (y/n): ").strip().lower()
        return response in ['y', 'yes']


def main():
    """Main entry point"""
    try:
        # Check for config file
        config_path = "config/config.yaml"
        if not Path(config_path).exists():
            print_error(f"Config file not found: {config_path}")
            print_info("Please create config/config.yaml from the template")
            sys.exit(1)

        # Check for API key
        if not os.getenv('OPENAI_API_KEY'):
            print_error("OPENAI_API_KEY environment variable not set")
            print_info("Set your OpenAI API key:")
            print_info("  export OPENAI_API_KEY='your-api-key-here'")
            sys.exit(1)

        # Start tool
        tool = LocatorTool(config_path)
        tool.start()

    except KeyboardInterrupt:
        print_info("\nExiting...")
    except Exception as e:
        print_error(f"Fatal error: {e}")
        logger.exception("Fatal error")
        sys.exit(1)


if __name__ == "__main__":
    main()
