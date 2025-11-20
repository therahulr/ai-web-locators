"""
Locator Generator Module
Handles locator creation, validation, and Python file generation
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class LocatorGenerator:
    """Generates and validates locators, creates Python locator files"""

    def __init__(self, browser_manager, config: Dict[str, Any]):
        """
        Initialize locator generator

        Args:
            browser_manager: BrowserManager instance for validation
            config: Locator configuration
        """
        self.browser = browser_manager
        self.config = config
        self.locators: Dict[str, List[Tuple[str, str]]] = {}  # page_name -> [(name, locator)]
        self.dynamic_locators: Dict[str, List[Dict[str, Any]]] = {}  # page_name -> [dynamic_locator_info]
        self.validation_results: List[Dict[str, Any]] = []

    def validate_element(self, name: str, locator_type: str, locator_value: str) -> Dict[str, Any]:
        """
        Validate a single locator

        Args:
            name: Locator name
            locator_type: Type (id, xpath, css)
            locator_value: Locator value

        Returns:
            Validation result
        """
        try:
            logger.info(f"Validating locator: {name}")

            result = self.browser.validate_locator(
                locator_type,
                locator_value,
                timeout=self.config.get('validation_timeout', 5000)
            )

            result['name'] = name
            result['timestamp'] = datetime.now().isoformat()

            self.validation_results.append(result)

            if result['valid']:
                logger.info(f"✓ {name} is valid")
            else:
                logger.warning(f"✗ {name} is invalid: {result.get('error', 'Unknown error')}")

            return result

        except Exception as e:
            logger.error(f"Validation failed for {name}: {e}")
            return {
                'name': name,
                'valid': False,
                'error': str(e)
            }

    def validate_batch(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate multiple locators

        Args:
            elements: List of elements from AI analysis

        Returns:
            List of validation results
        """
        logger.info(f"Validating {len(elements)} locators...")

        results = []
        for element in elements:
            result = self.validate_element(
                element['name'],
                element['locator_type'],
                element['locator_value']
            )
            results.append(result)

        valid_count = sum(1 for r in results if r['valid'])
        logger.info(f"Validation complete: {valid_count}/{len(results)} valid")

        return results

    def add_locator(self, page_name: str, name: str, locator_type: str, locator_value: str) -> None:
        """
        Add validated locator to collection

        Args:
            page_name: Page name for grouping
            name: Locator name
            locator_type: Type (id, xpath, css)
            locator_value: Locator value
        """
        if page_name not in self.locators:
            self.locators[page_name] = []

        self.locators[page_name].append({
            'name': name,
            'locator_type': locator_type,
            'locator_value': locator_value
        })

        logger.debug(f"Added locator: {page_name}.{name}")

    def add_dynamic_locator(self, page_name: str, locator_info: Dict[str, Any]) -> None:
        """
        Add dynamic/parameterized locator

        Args:
            page_name: Page name for grouping
            locator_info: Dynamic locator information
        """
        if page_name not in self.dynamic_locators:
            self.dynamic_locators[page_name] = []

        self.dynamic_locators[page_name].append(locator_info)
        logger.debug(f"Added dynamic locator: {page_name}.{locator_info['name']}")

    def generate_python_file(self, page_name: str, output_path: Path) -> str:
        """
        Generate Python locator file

        Args:
            page_name: Page name
            output_path: Output file path

        Returns:
            Generated file path
        """
        try:
            logger.info(f"Generating locator file for: {page_name}")

            # Convert page name to class name
            class_name = self._to_class_name(page_name) + "Locators"

            # Get locators for this page
            page_locators = self.locators.get(page_name, [])
            page_dynamic = self.dynamic_locators.get(page_name, [])

            if not page_locators and not page_dynamic:
                logger.warning(f"No locators found for page: {page_name}")
                return ""

            # Generate file content
            content = self._generate_file_content(class_name, page_locators, page_dynamic)

            # Write to file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content)

            logger.info(f"Locator file generated: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Failed to generate Python file: {e}")
            raise

    def _to_class_name(self, page_name: str) -> str:
        """Convert page name to PascalCase class name"""
        # Remove special characters and split
        parts = page_name.replace('_', ' ').replace('-', ' ').split()
        # Capitalize each part
        return ''.join(word.capitalize() for word in parts)

    def _generate_file_content(
        self,
        class_name: str,
        locators: List[Dict[str, Any]],
        dynamic_locators: List[Dict[str, Any]]
    ) -> str:
        """Generate Python file content"""

        lines = [
            '"""',
            f'Locator file for {class_name}',
            f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            '"""',
            '',
            'from typing import Tuple',
            '',
            '',
            f'class {class_name}:',
            '    """Page locators"""',
            ''
        ]

        # Add static locators
        if locators:
            lines.append('    # Static Locators')
            for loc in locators:
                lines.append(
                    f"    {loc['name']} = ('{loc['locator_type']}', \"{loc['locator_value']}\")"
                )
            lines.append('')

        # Add dynamic locators
        if dynamic_locators:
            lines.append('    # Dynamic Locators')
            for dloc in dynamic_locators:
                params = ', '.join([f"{p}: str" for p in dloc['parameters']])
                lines.append('    @staticmethod')
                lines.append(f"    def {dloc['name']}({params}) -> Tuple[str, str]:")
                lines.append(f"        \"\"\"{dloc.get('description', 'Dynamic locator')}\"\"\"")

                # Determine locator type from template
                template = dloc['template']
                if template.startswith('//') or template.startswith('(//'):
                    locator_type = 'xpath'
                elif '#' in template or '.' in template or '[' in template:
                    locator_type = 'css'
                else:
                    locator_type = 'xpath'

                # Generate f-string
                lines.append(f"        return ('{locator_type}', f\"{template}\")")
                lines.append('')

        return '\n'.join(lines)

    def get_validation_summary(self) -> Dict[str, Any]:
        """
        Get validation statistics

        Returns:
            Summary of validation results
        """
        total = len(self.validation_results)
        valid = sum(1 for r in self.validation_results if r['valid'])
        invalid = total - valid

        return {
            'total': total,
            'valid': valid,
            'invalid': invalid,
            'success_rate': (valid / total * 100) if total > 0 else 0
        }

    def clear(self) -> None:
        """Clear all stored locators"""
        self.locators.clear()
        self.dynamic_locators.clear()
        self.validation_results.clear()
        logger.info("Locator storage cleared")
