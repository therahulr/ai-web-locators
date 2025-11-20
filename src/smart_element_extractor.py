"""
Smart Element Extractor Module
Extracts interactive elements as structured JSON for AI processing
"""

import logging
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)


class SmartElementExtractor:
    """Extracts interactive elements from DOM as structured JSON"""

    def __init__(self):
        """Initialize extractor"""
        self.soup: Optional[BeautifulSoup] = None
        self.elements: List[Dict[str, Any]] = []

    def extract_from_html(self, html: str) -> List[Dict[str, Any]]:
        """
        Extract all interactive elements from HTML

        Args:
            html: Raw HTML content

        Returns:
            List of structured element dictionaries
        """
        try:
            logger.info("Extracting structured elements from DOM...")
            self.soup = BeautifulSoup(html, 'html.parser')
            self.elements = []

            # Extract different element types
            self._extract_inputs()
            self._extract_buttons()
            self._extract_links()
            self._extract_selects()
            self._extract_textareas()

            logger.info(f"Extracted {len(self.elements)} interactive elements")
            return self.elements

        except Exception as e:
            logger.error(f"Element extraction failed: {e}")
            raise

    def _extract_inputs(self) -> None:
        """Extract all input fields"""
        inputs = self.soup.find_all('input')

        for idx, inp in enumerate(inputs):
            input_type = inp.get('type', 'text').lower()

            # Skip hidden inputs
            if input_type == 'hidden':
                continue

            element = {
                'index': len(self.elements),
                'tag': 'input',
                'type': input_type,
                'id': inp.get('id'),
                'name': inp.get('name'),
                'placeholder': inp.get('placeholder'),
                'value': inp.get('value'),
                'aria_label': inp.get('aria-label'),
                'label': self._find_label_text(inp),
                'xpath': self._generate_xpath(inp),
                'css': self._generate_css(inp),
                'description': self._generate_description(inp, input_type)
            }

            self.elements.append(element)

    def _extract_buttons(self) -> None:
        """Extract all buttons"""
        # Button tags
        buttons = self.soup.find_all('button')

        for btn in buttons:
            element = {
                'index': len(self.elements),
                'tag': 'button',
                'type': 'button',
                'id': btn.get('id'),
                'name': btn.get('name'),
                'text': btn.get_text(strip=True),
                'aria_label': btn.get('aria-label'),
                'value': btn.get('value'),
                'xpath': self._generate_xpath(btn),
                'css': self._generate_css(btn),
                'description': self._generate_description(btn, 'button')
            }

            self.elements.append(element)

        # Input submit/button types
        submit_inputs = self.soup.find_all('input', type=['submit', 'button'])

        for inp in submit_inputs:
            element = {
                'index': len(self.elements),
                'tag': 'input',
                'type': inp.get('type'),
                'id': inp.get('id'),
                'name': inp.get('name'),
                'text': inp.get('value', ''),
                'aria_label': inp.get('aria-label'),
                'value': inp.get('value'),
                'xpath': self._generate_xpath(inp),
                'css': self._generate_css(inp),
                'description': self._generate_description(inp, 'button')
            }

            self.elements.append(element)

    def _extract_links(self) -> None:
        """Extract all links"""
        links = self.soup.find_all('a', href=True)

        for link in links:
            link_text = link.get_text(strip=True)

            # Skip empty links or purely icon links
            if not link_text or len(link_text) < 2:
                continue

            element = {
                'index': len(self.elements),
                'tag': 'a',
                'type': 'link',
                'id': link.get('id'),
                'name': link.get('name'),
                'text': link_text,
                'href': link.get('href'),
                'aria_label': link.get('aria-label'),
                'xpath': self._generate_xpath(link),
                'css': self._generate_css(link),
                'description': self._generate_description(link, 'link')
            }

            self.elements.append(element)

    def _extract_selects(self) -> None:
        """Extract all dropdowns/selects"""
        selects = self.soup.find_all('select')

        for sel in selects:
            # Get options
            options = [opt.get_text(strip=True) for opt in sel.find_all('option')]

            element = {
                'index': len(self.elements),
                'tag': 'select',
                'type': 'dropdown',
                'id': sel.get('id'),
                'name': sel.get('name'),
                'aria_label': sel.get('aria-label'),
                'label': self._find_label_text(sel),
                'options': options[:10],  # Limit to first 10 options
                'options_count': len(options),
                'xpath': self._generate_xpath(sel),
                'css': self._generate_css(sel),
                'description': self._generate_description(sel, 'dropdown')
            }

            self.elements.append(element)

    def _extract_textareas(self) -> None:
        """Extract all textareas"""
        textareas = self.soup.find_all('textarea')

        for ta in textareas:
            element = {
                'index': len(self.elements),
                'tag': 'textarea',
                'type': 'textarea',
                'id': ta.get('id'),
                'name': ta.get('name'),
                'placeholder': ta.get('placeholder'),
                'aria_label': ta.get('aria-label'),
                'label': self._find_label_text(ta),
                'xpath': self._generate_xpath(ta),
                'css': self._generate_css(ta),
                'description': self._generate_description(ta, 'textarea')
            }

            self.elements.append(element)

    def _find_label_text(self, element) -> Optional[str]:
        """Find associated label text for an element"""
        try:
            # Method 1: Label with 'for' attribute
            element_id = element.get('id')
            if element_id:
                label = self.soup.find('label', attrs={'for': element_id})
                if label:
                    return label.get_text(strip=True)

            # Method 2: Label wrapping element
            parent = element.parent
            if parent and parent.name == 'label':
                return parent.get_text(strip=True)

            # Method 3: Check aria-labelledby
            labelledby = element.get('aria-labelledby')
            if labelledby:
                label_elem = self.soup.find(id=labelledby)
                if label_elem:
                    return label_elem.get_text(strip=True)

            return None

        except Exception:
            return None

    def _generate_xpath(self, element) -> str:
        """Generate XPath for element"""
        try:
            # Prefer ID-based XPath
            element_id = element.get('id')
            if element_id:
                return f"//{element.name}[@id='{element_id}']"

            # Use name attribute
            element_name = element.get('name')
            if element_name:
                return f"//{element.name}[@name='{element_name}']"

            # Use type for inputs
            if element.name == 'input':
                input_type = element.get('type', 'text')
                return f"//input[@type='{input_type}']"

            # For links with text
            if element.name == 'a':
                text = element.get_text(strip=True)
                if text:
                    return f"//a[contains(text(), '{text[:30]}')]"

            # Fallback: position-based
            return f"//{element.name}"

        except Exception:
            return f"//{element.name}"

    def _generate_css(self, element) -> Optional[str]:
        """Generate CSS selector for element"""
        try:
            # Prefer ID
            element_id = element.get('id')
            if element_id:
                return f"#{element_id}"

            # Use name
            element_name = element.get('name')
            if element_name:
                return f"{element.name}[name='{element_name}']"

            # Use type for inputs
            if element.name == 'input':
                input_type = element.get('type', 'text')
                return f"input[type='{input_type}']"

            return None

        except Exception:
            return None

    def _generate_description(self, element, elem_type: str) -> str:
        """Generate human-readable description"""
        try:
            label = self._find_label_text(element)
            text = element.get_text(strip=True) if hasattr(element, 'get_text') else ''
            placeholder = element.get('placeholder', '')

            if label:
                return f"{label} {elem_type}"
            elif text:
                return f"{text} {elem_type}"
            elif placeholder:
                return f"{placeholder} {elem_type}"
            else:
                element_id = element.get('id', element.get('name', 'unknown'))
                return f"{element_id} {elem_type}"

        except Exception:
            return f"{elem_type}"

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of extracted elements

        Returns:
            Summary statistics
        """
        summary = {
            'total_elements': len(self.elements),
            'by_type': {},
            'elements_with_id': 0,
            'elements_with_name': 0,
            'elements_with_label': 0
        }

        for elem in self.elements:
            elem_type = elem.get('type', elem.get('tag'))

            # Count by type
            if elem_type in summary['by_type']:
                summary['by_type'][elem_type] += 1
            else:
                summary['by_type'][elem_type] = 1

            # Count identifiable elements
            if elem.get('id'):
                summary['elements_with_id'] += 1
            if elem.get('name'):
                summary['elements_with_name'] += 1
            if elem.get('label'):
                summary['elements_with_label'] += 1

        return summary
