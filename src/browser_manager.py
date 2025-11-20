"""
Browser Manager Module
Handles Playwright and Selenium browser automation with iframe/shadow DOM support
"""

import logging
from typing import Optional, Dict, Any, List
from playwright.sync_api import sync_playwright, Browser, Page, Playwright
import base64
from pathlib import Path

logger = logging.getLogger(__name__)


class BrowserManager:
    """Manages browser automation using Playwright"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize browser manager

        Args:
            config: Browser configuration from config.yaml
        """
        self.config = config
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.current_url: str = ""
        self.current_title: str = ""

    def launch(self) -> None:
        """Launch browser and create new page"""
        try:
            logger.info("Launching browser...")
            self.playwright = sync_playwright().start()

            browser_type = self.playwright.chromium
            self.browser = browser_type.launch(
                headless=self.config.get('headless', False),
                args=['--start-maximized']
            )

            context = self.browser.new_context(
                viewport={'width': self.config['window_size'][0],
                         'height': self.config['window_size'][1]},
                ignore_https_errors=True
            )

            self.page = context.new_page()
            self.page.set_default_timeout(self.config.get('timeout', 30000))

            logger.info("Browser launched successfully")

        except Exception as e:
            logger.error(f"Failed to launch browser: {e}")
            raise

    def navigate(self, url: str) -> None:
        """
        Navigate to URL

        Args:
            url: Target URL
        """
        try:
            if not self.page:
                raise RuntimeError("Browser not launched")

            logger.info(f"Navigating to: {url}")
            self.page.goto(url, wait_until='networkidle', timeout=60000)
            self.update_page_info()

        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            raise

    def update_page_info(self) -> None:
        """Update current page URL and title"""
        if self.page:
            self.current_url = self.page.url
            self.current_title = self.page.title()
            logger.debug(f"Page info updated - URL: {self.current_url}, Title: {self.current_title}")

    def capture_screenshot(self, output_path: Optional[Path] = None) -> str:
        """
        Capture full page screenshot

        Args:
            output_path: Optional path to save screenshot

        Returns:
            Base64 encoded screenshot
        """
        try:
            if not self.page:
                raise RuntimeError("Browser not launched")

            logger.info("Capturing screenshot...")
            screenshot_bytes = self.page.screenshot(full_page=True, type='png')

            if output_path:
                output_path.write_bytes(screenshot_bytes)
                logger.debug(f"Screenshot saved to: {output_path}")

            base64_screenshot = base64.b64encode(screenshot_bytes).decode('utf-8')
            logger.info("Screenshot captured successfully")
            return base64_screenshot

        except Exception as e:
            logger.error(f"Screenshot capture failed: {e}")
            raise

    def get_dom(self) -> str:
        """
        Extract full DOM HTML including iframes

        Returns:
            Complete HTML content
        """
        try:
            if not self.page:
                raise RuntimeError("Browser not launched")

            logger.info("Extracting DOM...")

            # Main page HTML
            main_html = self.page.content()

            # Extract iframe content
            iframes = self.page.frames
            iframe_contents = []

            for iframe in iframes:
                try:
                    iframe_html = iframe.content()
                    iframe_contents.append(f"\n<!-- IFRAME START -->\n{iframe_html}\n<!-- IFRAME END -->\n")
                except Exception as e:
                    logger.warning(f"Could not extract iframe content: {e}")

            full_html = main_html + "".join(iframe_contents)
            logger.info(f"DOM extracted successfully - Size: {len(full_html)} chars")
            return full_html

        except Exception as e:
            logger.error(f"DOM extraction failed: {e}")
            raise

    def validate_locator(self, locator_type: str, locator_value: str, timeout: int = 5000) -> Dict[str, Any]:
        """
        Validate locator on current page

        Args:
            locator_type: Type of locator (id, xpath, css)
            locator_value: Locator value
            timeout: Validation timeout in ms

        Returns:
            Validation result with element count and status
        """
        try:
            if not self.page:
                raise RuntimeError("Browser not launched")

            logger.debug(f"Validating locator: {locator_type}={locator_value}")

            # Map locator type to Playwright selector
            if locator_type == 'id':
                selector = f"#{locator_value}"
            elif locator_type == 'xpath':
                selector = f"xpath={locator_value}"
            elif locator_type == 'css':
                selector = locator_value
            else:
                return {
                    'valid': False,
                    'count': 0,
                    'error': f"Unknown locator type: {locator_type}"
                }

            # Count elements
            elements = self.page.locator(selector)
            count = elements.count()

            is_valid = count == 1

            result = {
                'valid': is_valid,
                'count': count,
                'locator_type': locator_type,
                'locator_value': locator_value,
                'error': None
            }

            if count == 0:
                result['error'] = "No elements found"
            elif count > 1:
                result['error'] = f"Multiple elements found ({count})"

            logger.debug(f"Validation result: {result}")
            return result

        except Exception as e:
            logger.error(f"Locator validation failed: {e}")
            return {
                'valid': False,
                'count': 0,
                'error': str(e)
            }

    def execute_script(self, script: str) -> Any:
        """
        Execute JavaScript in browser

        Args:
            script: JavaScript code

        Returns:
            Script execution result
        """
        try:
            if not self.page:
                raise RuntimeError("Browser not launched")

            result = self.page.evaluate(script)
            return result

        except Exception as e:
            logger.error(f"Script execution failed: {e}")
            raise

    def get_page_metadata(self) -> Dict[str, Any]:
        """
        Get current page metadata

        Returns:
            Page metadata including URL, title, dimensions
        """
        try:
            if not self.page:
                raise RuntimeError("Browser not launched")

            self.update_page_info()

            viewport = self.page.viewport_size

            metadata = {
                'url': self.current_url,
                'title': self.current_title,
                'viewport': viewport,
                'user_agent': self.page.evaluate('navigator.userAgent')
            }

            return metadata

        except Exception as e:
            logger.error(f"Failed to get page metadata: {e}")
            raise

    def close(self) -> None:
        """Close browser and cleanup"""
        try:
            logger.info("Closing browser...")

            if self.page:
                self.page.close()

            if self.browser:
                self.browser.close()

            if self.playwright:
                self.playwright.stop()

            logger.info("Browser closed successfully")

        except Exception as e:
            logger.error(f"Error closing browser: {e}")

    def __enter__(self):
        """Context manager entry"""
        self.launch()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
