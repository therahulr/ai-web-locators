"""
AI Engine Module
Handles OpenAI API integration for element analysis and locator generation
"""

import logging
import json
from typing import Dict, Any, List, Optional
import openai
from openai import OpenAI

logger = logging.getLogger(__name__)


class AIEngine:
    """Manages OpenAI API interactions for intelligent locator generation"""

    SYSTEM_PROMPT = """You are an expert QA automation engineer specializing in web element identification and locator generation.

Your task is to analyze provided screenshots and DOM HTML to identify interactive elements and generate optimal locators.

**Locator Strategy Priority:**
1. ID (best - unique and stable)
2. XPath (good - flexible and precise)
3. CSS (good - fast and readable)
4. Name attribute (acceptable for form fields)

**IMPORTANT RULES:**
- ALWAYS use "id", "xpath", "css", or "name" as locator_type
- NEVER use "link_text" or "partial_link_text" - use xpath instead
- For links: use xpath like `//a[text()='Link Text']` or `//a[contains(text(), 'Link')]`
- Prefer unique attributes (id, name) over text-based locators when available

**Naming Conventions:**
- Use ALL_CAPS_SNAKE_CASE
- Be descriptive: "NEW_APPLICATION_LINK" not "LINK_1"
- Include element type suffix: _BUTTON, _INPUT, _LINK, _CHECKBOX, _DROPDOWN, _TEXTAREA
- Examples:
  - USERNAME_INPUT
  - LOGIN_BUTTON
  - FORGOT_PASSWORD_LINK
  - REMEMBER_ME_CHECKBOX
  - COUNTRY_DROPDOWN

**For Dynamic/Repeated Elements:**
Create parameterized locators using Python f-strings:
- Example: `checkbox_by_name(name: str)` → `//input[@type='checkbox' and @name='{name}']`

**Output Format (JSON):**
{
  "elements": [
    {
      "name": "USERNAME_INPUT",
      "locator_type": "id",
      "locator_value": "username",
      "element_type": "input",
      "description": "Username text input field",
      "is_unique": true,
      "alternatives": []
    }
  ],
  "dynamic_locators": [
    {
      "name": "checkbox_by_label",
      "template": "//input[@type='checkbox' and following-sibling::label[text()='{label}']]",
      "parameters": ["label"],
      "description": "Checkbox by label text"
    }
  ],
  "page_sections": ["Header", "Login Form", "Footer"],
  "recommendations": ["Consider adding data-testid attributes for better stability"]
}"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize AI Engine

        Args:
            config: OpenAI configuration
        """
        self.config = config
        api_key = config.get('api_key')

        if not api_key:
            raise ValueError("OpenAI API key not provided")

        self.client = OpenAI(api_key=api_key)
        self.model = config.get('model', 'gpt-4o')
        self.max_tokens = config.get('max_tokens', 4000)
        self.temperature = config.get('temperature', 0.3)

        logger.info(f"AI Engine initialized with model: {self.model}")

    def generate_locators_from_elements(
        self,
        screenshot_base64: str,
        elements_json: List[Dict[str, Any]],
        url: str
    ) -> Dict[str, Any]:
        """
        Generate Python locators from structured element JSON (Phase 1)

        Args:
            screenshot_base64: Base64 encoded screenshot
            elements_json: List of structured element dictionaries
            url: Current page URL

        Returns:
            Locator definitions
        """
        try:
            logger.info(f"Generating locators for {len(elements_json)} elements...")

            prompt = f"""Analyze the screenshot and structured element data to generate Python locators.

**Page URL:** {url}

**Elements (JSON):**
```json
{json.dumps(elements_json, indent=2)}
```

**Task:**
1. For each element, generate a Python locator name following naming conventions
2. Choose optimal locator strategy (prefer ID > Name > XPath > CSS)
3. Use the xpath/css provided in JSON or improve if needed
4. Generate descriptive names: USERNAME_INPUT, CONTRACTOR_DROPDOWN, LOGIN_BUTTON

**RULES:**
- locator_type must be: "id", "xpath", "css", or "name"
- Names: ALL_CAPS_SNAKE_CASE with element type suffix
- Use element 'label' or 'text' or 'description' to create meaningful names
- If element has label "Contractor", name it "CONTRACTOR_DROPDOWN"

**Output JSON:**
{{
  "elements": [
    {{
      "element_index": 0,
      "name": "USERNAME_INPUT",
      "locator_type": "id",
      "locator_value": "username",
      "element_type": "input",
      "description": "Username text input field"
    }}
  ]
}}
"""

            messages = [
                {
                    "role": "system",
                    "content": "You are an expert QA engineer. Generate Python locators from structured element data."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{screenshot_base64}",
                                "detail": "high"
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )

            result_text = response.choices[0].message.content
            result = json.loads(result_text)

            logger.info(f"Generated {len(result.get('elements', []))} locators")
            return result

        except Exception as e:
            logger.error(f"Locator generation failed: {e}")
            raise

    def generate_natural_language_steps(
        self,
        screenshot_base64: str,
        elements_summary: List[Dict[str, str]],
        url: str,
        page_title: str
    ) -> Dict[str, Any]:
        """
        Generate natural language test steps (Phase 2)

        Args:
            screenshot_base64: Base64 encoded screenshot
            elements_summary: List of element summaries with labels
            url: Current page URL
            page_title: Page title

        Returns:
            Natural language test steps
        """
        try:
            logger.info("Generating natural language test steps...")

            # Create element summary
            element_descriptions = []
            for elem in elements_summary:
                elem_desc = f"- {elem.get('description', 'Unknown element')}"
                element_descriptions.append(elem_desc)

            elements_text = "\n".join(element_descriptions[:30])  # Limit to 30

            prompt = f"""Based on the screenshot and available elements, describe what a user would do on this page in natural, human-readable language.

**Page:** {page_title}
**URL:** {url}

**Available Elements:**
{elements_text}

**Task:**
Generate natural language test steps that describe the workflow a user would follow.

**Format Requirements:**
- Use natural language like "Select an option from Contractor dropdown"
- Include proper element names/labels from the screenshot
- Be specific: "Enter your username in the Username field" NOT "Enter text in input field"
- Focus on user actions, not technical locators
- Number steps sequentially

**Example Output:**
{{
  "title": "Sales Center Login",
  "steps": [
    {{
      "step_number": 1,
      "action": "Navigate to the Sales Center login page"
    }},
    {{
      "step_number": 2,
      "action": "Select a contractor from the Contractor dropdown field"
    }},
    {{
      "step_number": 3,
      "action": "Enter your username in the Username input field"
    }},
    {{
      "step_number": 4,
      "action": "Click the Login button to proceed"
    }}
  ],
  "validations": [
    "Verify the dashboard loads successfully",
    "Check that the user name appears in the header"
  ]
}}

**Return JSON in this exact format.**
"""

            messages = [
                {
                    "role": "system",
                    "content": "You are a QA documentation expert. Write clear, natural language test steps for end users."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{screenshot_base64}",
                                "detail": "high"
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=2000,
                temperature=0.4,
                response_format={"type": "json_object"}
            )

            result_text = response.choices[0].message.content
            result = json.loads(result_text)

            logger.info(f"Generated {len(result.get('steps', []))} natural language steps")
            return result

        except Exception as e:
            logger.error(f"Natural language step generation failed: {e}")
            raise

    def analyze_page(
        self,
        screenshot_base64: str,
        dom_html: str,
        url: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze page and generate locators

        Args:
            screenshot_base64: Base64 encoded screenshot
            dom_html: Cleaned DOM HTML
            url: Current page URL
            context: Optional conversation context

        Returns:
            AI analysis result with locators
        """
        try:
            logger.info(f"Analyzing page: {url}")

            user_prompt = f"""Analyze this web page and generate optimal locators.

**Page URL:** {url}

**DOM HTML:**
```html
{dom_html[:30000]}
```

**Task:**
1. Identify ALL interactive elements (buttons, inputs, links, checkboxes, dropdowns, etc.)
2. Generate pythonic locator names following naming conventions
3. Choose optimal locator strategy (ID > XPath > CSS)
4. For repeated elements (lists, tables), create dynamic f-string locators
5. Identify page sections and structure

**Return valid JSON only** matching the output format specified in system prompt.
"""

            if context:
                user_prompt = f"**Previous Context:**\n{context}\n\n" + user_prompt

            messages = [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{screenshot_base64}",
                                "detail": "high"
                            }
                        },
                        {
                            "type": "text",
                            "text": user_prompt
                        }
                    ]
                }
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )

            result_text = response.choices[0].message.content
            result = json.loads(result_text)

            logger.info(f"Analysis complete - Found {len(result.get('elements', []))} elements")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            raise
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            raise

    def generate_test_steps(
        self,
        screenshot_base64: str,
        dom_html: str,
        url: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate test steps for current workflow

        Args:
            screenshot_base64: Base64 encoded screenshot
            dom_html: Cleaned DOM HTML
            url: Current page URL
            context: Optional conversation context

        Returns:
            Test steps and documentation
        """
        try:
            logger.info("Generating test steps...")

            user_prompt = f"""Based on this page, generate comprehensive test steps.

**Page URL:** {url}

**DOM HTML:**
```html
{dom_html[:20000]}
```

**Task:**
Generate detailed test steps including:
1. Navigation steps
2. Actions to perform (click, input, select, etc.)
3. Validation points
4. Expected outcomes

**Return JSON:**
{{
  "title": "Page/Feature Name",
  "steps": [
    {{
      "step_number": 1,
      "action": "Navigate to login page",
      "locator": "N/A",
      "description": "Open browser and navigate to login URL"
    }}
  ],
  "validations": ["Check page title", "Verify login button is visible"],
  "prerequisites": ["User account exists", "Browser is configured"]
}}
"""

            if context:
                user_prompt = f"**Previous Context:**\n{context}\n\n" + user_prompt

            messages = [
                {"role": "system", "content": "You are a QA test documentation expert. Generate clear, actionable test steps."},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{screenshot_base64}",
                                "detail": "high"
                            }
                        },
                        {
                            "type": "text",
                            "text": user_prompt
                        }
                    ]
                }
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )

            result_text = response.choices[0].message.content
            result = json.loads(result_text)

            logger.info("Test steps generated successfully")
            return result

        except Exception as e:
            logger.error(f"Test step generation failed: {e}")
            raise

    def answer_question(
        self,
        question: str,
        screenshot_base64: str,
        dom_html: str,
        url: str,
        context: Optional[str] = None
    ) -> str:
        """
        Answer natural language question about the page

        Args:
            question: User question
            screenshot_base64: Base64 encoded screenshot
            dom_html: Cleaned DOM HTML
            url: Current page URL
            context: Optional conversation context

        Returns:
            AI answer
        """
        try:
            logger.info(f"Answering question: {question}")

            user_prompt = f"""Answer the following question about this web page.

**Page URL:** {url}

**Question:** {question}

**DOM HTML:**
```html
{dom_html[:20000]}
```

Provide a detailed, technical answer suitable for a QA automation engineer.
"""

            if context:
                user_prompt = f"**Previous Context:**\n{context}\n\n" + user_prompt

            messages = [
                {"role": "system", "content": "You are a helpful QA automation assistant. Answer questions clearly and technically."},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{screenshot_base64}",
                                "detail": "high"
                            }
                        },
                        {
                            "type": "text",
                            "text": user_prompt
                        }
                    ]
                }
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=2000,
                temperature=self.temperature
            )

            answer = response.choices[0].message.content

            logger.info("Question answered successfully")
            return answer

        except Exception as e:
            logger.error(f"Question answering failed: {e}")
            raise

    def identify_page_sections(
        self,
        screenshot_base64: str,
        dom_html: str
    ) -> List[str]:
        """
        Identify major page sections

        Args:
            screenshot_base64: Base64 encoded screenshot
            dom_html: Cleaned DOM HTML

        Returns:
            List of page sections
        """
        try:
            logger.info("Identifying page sections...")

            user_prompt = f"""Identify the major sections of this web page.

**DOM HTML:**
```html
{dom_html[:15000]}
```

Return JSON:
{{
  "sections": ["Header", "Navigation Menu", "Main Content", "Login Form", "Footer"]
}}
"""

            messages = [
                {"role": "system", "content": "You are a web page structure analyst."},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{screenshot_base64}",
                                "detail": "high"
                            }
                        },
                        {
                            "type": "text",
                            "text": user_prompt
                        }
                    ]
                }
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=1000,
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )

            result_text = response.choices[0].message.content
            result = json.loads(result_text)

            sections = result.get('sections', [])
            logger.info(f"Identified {len(sections)} sections")
            return sections

        except Exception as e:
            logger.error(f"Section identification failed: {e}")
            return []
