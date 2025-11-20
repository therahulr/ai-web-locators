"""
File Manager Module
Handles all file I/O operations for locators, documentation, and session data
"""

import logging
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class FileManager:
    """Manages file operations for the tool"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize file manager

        Args:
            config: Output configuration
        """
        self.config = config
        self.locators_dir = Path(config['locators_dir'])
        self.docs_dir = Path(config['docs_dir'])
        self.sessions_dir = Path(config['sessions_dir'])

        # Create directories
        self._create_directories()

    def _create_directories(self) -> None:
        """Create output directories if they don't exist"""
        try:
            self.locators_dir.mkdir(parents=True, exist_ok=True)
            self.docs_dir.mkdir(parents=True, exist_ok=True)
            self.sessions_dir.mkdir(parents=True, exist_ok=True)
            logger.debug("Output directories verified")

        except Exception as e:
            logger.error(f"Failed to create directories: {e}")
            raise

    def save_session(self, session_data: Dict[str, Any], session_id: Optional[str] = None) -> str:
        """
        Save session data to JSON

        Args:
            session_data: Session data to save
            session_id: Optional session ID (generates timestamp-based if not provided)

        Returns:
            Session file path
        """
        try:
            if not session_id:
                session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

            session_file = self.sessions_dir / f"session_{session_id}.json"

            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Session saved: {session_file}")
            return str(session_file)

        except Exception as e:
            logger.error(f"Failed to save session: {e}")
            raise

    def load_session(self, session_id: str) -> Dict[str, Any]:
        """
        Load session data from JSON

        Args:
            session_id: Session ID or file path

        Returns:
            Session data
        """
        try:
            if session_id.endswith('.json'):
                session_file = Path(session_id)
            else:
                session_file = self.sessions_dir / f"session_{session_id}.json"

            if not session_file.exists():
                raise FileNotFoundError(f"Session file not found: {session_file}")

            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)

            logger.info(f"Session loaded: {session_file}")
            return session_data

        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            raise

    def save_markdown_doc(self, content: str, filename: str) -> str:
        """
        Save markdown documentation

        Args:
            content: Markdown content
            filename: Output filename

        Returns:
            File path
        """
        try:
            if not filename.endswith('.md'):
                filename += '.md'

            doc_file = self.docs_dir / filename

            with open(doc_file, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"Documentation saved: {doc_file}")
            return str(doc_file)

        except Exception as e:
            logger.error(f"Failed to save documentation: {e}")
            raise

    def append_to_doc(self, content: str, filename: str) -> str:
        """
        Append content to existing markdown documentation

        Args:
            content: Content to append
            filename: Documentation filename

        Returns:
            File path
        """
        try:
            if not filename.endswith('.md'):
                filename += '.md'

            doc_file = self.docs_dir / filename

            with open(doc_file, 'a', encoding='utf-8') as f:
                f.write('\n' + content)

            logger.info(f"Content appended to: {doc_file}")
            return str(doc_file)

        except Exception as e:
            logger.error(f"Failed to append to documentation: {e}")
            raise

    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all saved sessions

        Returns:
            List of session metadata
        """
        try:
            sessions = []

            for session_file in self.sessions_dir.glob('session_*.json'):
                stat = session_file.stat()
                sessions.append({
                    'id': session_file.stem.replace('session_', ''),
                    'file': str(session_file),
                    'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    'size': stat.st_size
                })

            sessions.sort(key=lambda x: x['created'], reverse=True)

            logger.debug(f"Found {len(sessions)} sessions")
            return sessions

        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            return []

    def list_locator_files(self) -> List[str]:
        """
        List all generated locator files

        Returns:
            List of locator file paths
        """
        try:
            locator_files = [str(f) for f in self.locators_dir.glob('*_locators.py')]
            locator_files.sort()

            logger.debug(f"Found {len(locator_files)} locator files")
            return locator_files

        except Exception as e:
            logger.error(f"Failed to list locator files: {e}")
            return []

    def list_docs(self) -> List[str]:
        """
        List all documentation files

        Returns:
            List of documentation file paths
        """
        try:
            doc_files = [str(f) for f in self.docs_dir.glob('*.md')]
            doc_files.sort()

            logger.debug(f"Found {len(doc_files)} documentation files")
            return doc_files

        except Exception as e:
            logger.error(f"Failed to list documentation files: {e}")
            return []

    def export_validation_report(self, validation_results: List[Dict[str, Any]], filename: str) -> str:
        """
        Export validation results as JSON report

        Args:
            validation_results: List of validation results
            filename: Output filename

        Returns:
            Report file path
        """
        try:
            if not filename.endswith('.json'):
                filename += '.json'

            report_file = self.sessions_dir / filename

            report = {
                'generated_at': datetime.now().isoformat(),
                'total_validations': len(validation_results),
                'valid_count': sum(1 for r in validation_results if r.get('valid', False)),
                'invalid_count': sum(1 for r in validation_results if not r.get('valid', False)),
                'results': validation_results
            }

            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)

            logger.info(f"Validation report exported: {report_file}")
            return str(report_file)

        except Exception as e:
            logger.error(f"Failed to export validation report: {e}")
            raise

    def cleanup_old_sessions(self, days: int = 30) -> int:
        """
        Delete session files older than specified days

        Args:
            days: Age threshold in days

        Returns:
            Number of deleted files
        """
        try:
            threshold = datetime.now().timestamp() - (days * 24 * 3600)
            deleted_count = 0

            for session_file in self.sessions_dir.glob('session_*.json'):
                if session_file.stat().st_ctime < threshold:
                    session_file.unlink()
                    deleted_count += 1

            logger.info(f"Cleaned up {deleted_count} old session files")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup old sessions: {e}")
            return 0
