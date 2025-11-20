"""
DOM Analyzer Module
Processes and cleans DOM HTML for AI consumption
"""

import logging
import re
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class DOMAnalyzer:
    """Analyzes and processes DOM HTML"""

    def __init__(self):
        """Initialize DOM analyzer"""
        self.soup: Optional[BeautifulSoup] = None
        self.raw_html: str = ""
        self.cleaned_html: str = ""

    def load_html(self, html: str) -> None:
        """
        Load and parse HTML

        Args:
            html: Raw HTML content
        """
        try:
            logger.info("Loading HTML for analysis...")
            self.raw_html = html
            self.soup = BeautifulSoup(html, 'html.parser')
            logger.info(f"HTML loaded successfully - Size: {len(html)} chars")

        except Exception as e:
            logger.error(f"Failed to load HTML: {e}")
            raise

    def clean_html(self, max_size: int = 40000) -> str:
        """
        Clean HTML for AI processing by removing noise and focusing on interactive elements

        Args:
            max_size: Maximum HTML size in characters

        Returns:
            Cleaned and optimized HTML string
        """
        try:
            if not self.soup:
                raise RuntimeError("HTML not loaded")

            logger.info("Cleaning and optimizing DOM...")

            # Step 1: Remove noise tags completely
            for tag in self.soup(['script', 'style', 'noscript', 'svg', 'iframe', 'meta', 'link']):
                tag.decompose()

            # Step 2: Remove comments
            from bs4 import Comment
            for comment in self.soup.find_all(string=lambda text: isinstance(text, Comment)):
                comment.extract()

            # Step 3: Clean all tags - remove noise attributes
            noise_attrs = [
                'style', 'class', 'onclick', 'onchange', 'onload', 'onfocus', 'onblur',
                'data-v-', 'data-reactid', 'data-react-', '__reactProps',
                'aria-describedby', 'aria-controls', 'aria-expanded'
            ]

            for tag in self.soup.find_all(True):
                attrs_to_remove = []
                for attr in list(tag.attrs.keys()):
                    # Remove by exact match or prefix
                    if attr in noise_attrs or any(attr.startswith(prefix) for prefix in ['on', 'data-v-', 'data-react']):
                        attrs_to_remove.append(attr)

                for attr in attrs_to_remove:
                    del tag.attrs[attr]

            # Step 4: Extract only relevant sections (focus on forms, buttons, inputs)
            interactive_tags = ['form', 'input', 'button', 'select', 'textarea', 'a', 'label']
            relevant_sections = []

            # Find all interactive elements and their parent contexts
            for tag_name in interactive_tags:
                elements = self.soup.find_all(tag_name)
                for elem in elements:
                    # Get parent context (up to 2 levels)
                    parent = elem.parent
                    if parent and parent.name not in ['html', 'body']:
                        relevant_sections.append(parent)
                    else:
                        relevant_sections.append(elem)

            # Step 5: Build focused HTML from relevant sections
            if relevant_sections:
                focused_soup = BeautifulSoup('<body></body>', 'html.parser')
                seen_elements = set()

                for section in relevant_sections:
                    # Avoid duplicates
                    section_str = str(section)
                    if section_str not in seen_elements:
                        seen_elements.add(section_str)
                        focused_soup.body.append(section.extract() if hasattr(section, 'extract') else section)

                cleaned = str(focused_soup)
            else:
                # Fallback: use full cleaned DOM
                cleaned = str(self.soup)

            # Step 6: Aggressive whitespace compression
            cleaned = re.sub(r'\s+', ' ', cleaned)  # Multiple spaces to single
            cleaned = re.sub(r'>\s+<', '><', cleaned)  # Remove spaces between tags
            cleaned = re.sub(r'\n+', '\n', cleaned)  # Multiple newlines to single

            # Step 7: Intelligent truncation if still too large
            if len(cleaned) > max_size:
                logger.warning(f"DOM still large ({len(cleaned)} chars), applying smart truncation to {max_size}")

                # Try to find a good breaking point (end of a tag)
                truncate_pos = max_size - 100
                last_tag_close = cleaned.rfind('>', 0, truncate_pos)

                if last_tag_close > max_size // 2:  # If we found a reasonable breaking point
                    cleaned = cleaned[:last_tag_close + 1] + "\n<!-- DOM TRUNCATED FOR AI PROCESSING -->"
                else:
                    cleaned = cleaned[:max_size] + "\n<!-- DOM TRUNCATED FOR AI PROCESSING -->"

            self.cleaned_html = cleaned
            logger.info(f"DOM optimized successfully - Original: {len(self.raw_html)} chars → Optimized: {len(cleaned)} chars (saved {len(self.raw_html) - len(cleaned)} chars)")
            return cleaned

        except Exception as e:
            logger.error(f"HTML cleaning failed: {e}")
            raise

    def extract_interactive_elements(self) -> List[Dict[str, Any]]:
        """
        Extract interactive elements from DOM

        Returns:
            List of interactive elements with metadata
        """
        try:
            if not self.soup:
                raise RuntimeError("HTML not loaded")

            logger.info("Extracting interactive elements...")

            interactive_elements = []

            # Tags to extract
            interactive_tags = {
                'button': 'button',
                'input': 'input',
                'a': 'link',
                'select': 'dropdown',
                'textarea': 'textarea',
                '[role="button"]': 'button',
                '[onclick]': 'clickable',
                '[type="submit"]': 'button',
                '[type="checkbox"]': 'checkbox',
                '[type="radio"]': 'radio'
            }

            for selector, element_type in interactive_tags.items():
                elements = self.soup.select(selector)

                for elem in elements:
                    element_data = {
                        'tag': elem.name,
                        'type': element_type,
                        'id': elem.get('id'),
                        'name': elem.get('name'),
                        'placeholder': elem.get('placeholder'),
                        'aria_label': elem.get('aria-label'),
                        'text': elem.get_text(strip=True)[:100] if elem.get_text(strip=True) else None,
                        'attributes': {k: v for k, v in elem.attrs.items() if k in ['type', 'value', 'href', 'title']}
                    }

                    interactive_elements.append(element_data)

            logger.info(f"Extracted {len(interactive_elements)} interactive elements")
            return interactive_elements

        except Exception as e:
            logger.error(f"Failed to extract interactive elements: {e}")
            raise

    def identify_forms(self) -> List[Dict[str, Any]]:
        """
        Identify all forms on the page

        Returns:
            List of forms with their fields
        """
        try:
            if not self.soup:
                raise RuntimeError("HTML not loaded")

            logger.info("Identifying forms...")

            forms = []
            form_elements = self.soup.find_all('form')

            for idx, form in enumerate(form_elements):
                form_data = {
                    'index': idx,
                    'id': form.get('id'),
                    'name': form.get('name'),
                    'action': form.get('action'),
                    'method': form.get('method', 'get'),
                    'fields': []
                }

                # Extract form fields
                for field in form.find_all(['input', 'select', 'textarea']):
                    field_data = {
                        'tag': field.name,
                        'type': field.get('type', 'text'),
                        'name': field.get('name'),
                        'id': field.get('id'),
                        'placeholder': field.get('placeholder'),
                        'required': field.has_attr('required')
                    }
                    form_data['fields'].append(field_data)

                forms.append(form_data)

            logger.info(f"Identified {len(forms)} forms")
            return forms

        except Exception as e:
            logger.error(f"Failed to identify forms: {e}")
            raise

    def get_page_structure(self) -> Dict[str, Any]:
        """
        Analyze page structure and sections

        Returns:
            Page structure information
        """
        try:
            if not self.soup:
                raise RuntimeError("HTML not loaded")

            logger.info("Analyzing page structure...")

            structure = {
                'has_header': bool(self.soup.find(['header', '[role="banner"]'])),
                'has_nav': bool(self.soup.find(['nav', '[role="navigation"]'])),
                'has_main': bool(self.soup.find(['main', '[role="main"]'])),
                'has_footer': bool(self.soup.find(['footer', '[role="contentinfo"]'])),
                'has_sidebar': bool(self.soup.find(['aside', '[role="complementary"]'])),
                'headings': [h.get_text(strip=True) for h in self.soup.find_all(['h1', 'h2', 'h3'])[:10]],
                'forms_count': len(self.soup.find_all('form')),
                'buttons_count': len(self.soup.find_all(['button', '[type="submit"]'])),
                'links_count': len(self.soup.find_all('a')),
                'inputs_count': len(self.soup.find_all('input'))
            }

            logger.info(f"Page structure analyzed: {structure}")
            return structure

        except Exception as e:
            logger.error(f"Failed to analyze page structure: {e}")
            raise

    def sanitize_for_ai(self, html: str) -> str:
        """
        Sanitize HTML for AI processing (remove sensitive data)

        Args:
            html: HTML to sanitize

        Returns:
            Sanitized HTML
        """
        try:
            logger.debug("Sanitizing HTML for AI...")

            # Remove potential sensitive data patterns
            sanitized = re.sub(r'password["\']?\s*[:=]\s*["\'][^"\']*["\']', 'password="***"', html, flags=re.IGNORECASE)
            sanitized = re.sub(r'token["\']?\s*[:=]\s*["\'][^"\']*["\']', 'token="***"', sanitized, flags=re.IGNORECASE)
            sanitized = re.sub(r'api[_-]?key["\']?\s*[:=]\s*["\'][^"\']*["\']', 'api_key="***"', sanitized, flags=re.IGNORECASE)

            logger.debug("HTML sanitized successfully")
            return sanitized

        except Exception as e:
            logger.error(f"HTML sanitization failed: {e}")
            return html

    def get_xpath_for_element(self, element_id: str) -> Optional[str]:
        """
        Generate XPath for element by ID

        Args:
            element_id: Element ID

        Returns:
            XPath string or None
        """
        try:
            if not self.soup:
                raise RuntimeError("HTML not loaded")

            element = self.soup.find(id=element_id)
            if not element:
                return None

            # Simple XPath generation (can be enhanced)
            xpath_parts = []
            current = element

            while current and current.name:
                siblings = current.find_previous_siblings(current.name)
                index = len(siblings) + 1
                xpath_parts.insert(0, f"{current.name}[{index}]")
                current = current.parent

            xpath = "/" + "/".join(xpath_parts)
            return xpath

        except Exception as e:
            logger.error(f"Failed to generate XPath: {e}")
            return None
