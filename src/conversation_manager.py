"""
Conversation Manager Module
Maintains AI conversation context and history
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ConversationManager:
    """Manages AI conversation context and history"""

    def __init__(self, max_history: int = 20):
        """
        Initialize conversation manager

        Args:
            max_history: Maximum number of interactions to keep in context
        """
        self.max_history = max_history
        self.history: List[Dict[str, Any]] = []
        self.current_session: Dict[str, Any] = {
            'session_id': datetime.now().strftime("%Y%m%d_%H%M%S"),
            'started_at': datetime.now().isoformat(),
            'pages_visited': [],
            'locators_generated': [],
            'test_steps': [],
            'questions_asked': []
        }

    def add_interaction(
        self,
        interaction_type: str,
        data: Dict[str, Any],
        response: Optional[Any] = None
    ) -> None:
        """
        Add interaction to history

        Args:
            interaction_type: Type of interaction (analyze, question, steps, etc.)
            data: Interaction data
            response: AI response
        """
        try:
            interaction = {
                'timestamp': datetime.now().isoformat(),
                'type': interaction_type,
                'data': data,
                'response': response
            }

            self.history.append(interaction)

            # Trim history if too long
            if len(self.history) > self.max_history:
                self.history = self.history[-self.max_history:]

            logger.debug(f"Added {interaction_type} interaction to history")

        except Exception as e:
            logger.error(f"Failed to add interaction: {e}")

    def add_page_visit(self, url: str, title: str) -> None:
        """
        Record page visit

        Args:
            url: Page URL
            title: Page title
        """
        visit = {
            'url': url,
            'title': title,
            'timestamp': datetime.now().isoformat()
        }

        self.current_session['pages_visited'].append(visit)
        logger.debug(f"Page visit recorded: {url}")

    def add_locators(self, page_name: str, locators: List[str]) -> None:
        """
        Record generated locators

        Args:
            page_name: Page name
            locators: List of locator names
        """
        record = {
            'page': page_name,
            'locators': locators,
            'timestamp': datetime.now().isoformat()
        }

        self.current_session['locators_generated'].append(record)
        logger.debug(f"Recorded {len(locators)} locators for {page_name}")

    def add_test_steps(self, page_name: str, url: str, steps_data: Dict[str, Any]) -> None:
        """
        Record AI-generated test steps for a page

        Args:
            page_name: Page name
            url: Page URL
            steps_data: Test steps data from AI
        """
        record = {
            'page': page_name,
            'url': url,
            'steps': steps_data.get('steps', []),
            'title': steps_data.get('title', page_name),
            'prerequisites': steps_data.get('prerequisites', []),
            'validations': steps_data.get('validations', []),
            'timestamp': datetime.now().isoformat()
        }

        self.current_session['test_steps'].append(record)
        logger.debug(f"Recorded test steps for {page_name}")

    def add_question(self, question: str, answer: str) -> None:
        """
        Record Q&A interaction

        Args:
            question: User question
            answer: AI answer
        """
        qa = {
            'question': question,
            'answer': answer,
            'timestamp': datetime.now().isoformat()
        }

        self.current_session['questions_asked'].append(qa)
        logger.debug(f"Recorded Q&A interaction")

    def get_context_summary(self, max_chars: int = 2000) -> str:
        """
        Get summarized conversation context for AI

        Args:
            max_chars: Maximum context length

        Returns:
            Context summary string
        """
        try:
            if not self.history:
                return ""

            context_parts = []

            # Add recent page visits
            recent_pages = self.current_session['pages_visited'][-3:]
            if recent_pages:
                pages_text = "\n".join([f"- {p['title']} ({p['url']})" for p in recent_pages])
                context_parts.append(f"**Recent Pages:**\n{pages_text}")

            # Add recent locators
            recent_locators = self.current_session['locators_generated'][-2:]
            if recent_locators:
                locators_text = "\n".join([
                    f"- {loc['page']}: {', '.join(loc['locators'][:5])}"
                    for loc in recent_locators
                ])
                context_parts.append(f"**Recent Locators:**\n{locators_text}")

            # Add recent Q&A
            recent_qa = self.current_session['questions_asked'][-3:]
            if recent_qa:
                qa_text = "\n".join([f"Q: {qa['question']}\nA: {qa['answer'][:100]}..." for qa in recent_qa])
                context_parts.append(f"**Recent Q&A:**\n{qa_text}")

            context = "\n\n".join(context_parts)

            # Truncate if too long
            if len(context) > max_chars:
                context = context[:max_chars] + "\n..."

            return context

        except Exception as e:
            logger.error(f"Failed to generate context summary: {e}")
            return ""

    def get_full_history(self) -> List[Dict[str, Any]]:
        """
        Get complete interaction history

        Returns:
            Full history list
        """
        return self.history.copy()

    def get_session_data(self) -> Dict[str, Any]:
        """
        Get current session data

        Returns:
            Session data dictionary
        """
        return self.current_session.copy()

    def clear_history(self) -> None:
        """Clear conversation history"""
        self.history.clear()
        logger.info("Conversation history cleared")

    def reset_session(self) -> None:
        """Reset current session"""
        self.current_session = {
            'session_id': datetime.now().strftime("%Y%m%d_%H%M%S"),
            'started_at': datetime.now().isoformat(),
            'pages_visited': [],
            'locators_generated': [],
            'test_steps': [],
            'questions_asked': []
        }
        self.history.clear()
        logger.info("Session reset")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get session statistics

        Returns:
            Statistics dictionary
        """
        total_locators = sum(
            len(loc['locators'])
            for loc in self.current_session['locators_generated']
        )

        return {
            'session_id': self.current_session['session_id'],
            'started_at': self.current_session['started_at'],
            'pages_visited': len(self.current_session['pages_visited']),
            'total_locators': total_locators,
            'questions_asked': len(self.current_session['questions_asked']),
            'interactions': len(self.history)
        }
