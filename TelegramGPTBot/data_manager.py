"""
Data management utilities for local Q&A caching
Handles reading, writing, and updating the data.json file
"""
import json
import os
import logging
import threading
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class DataManager:
    def __init__(self, data_file: str = "data.json"):
        self.data_file = data_file
        self.lock = threading.Lock()  # Thread safety for file operations
        self._ensure_data_file()
    
    def _ensure_data_file(self):
        """Ensure data file exists with proper structure"""
        try:
            if not os.path.exists(self.data_file):
                self._create_initial_data_file()
            else:
                # Verify file integrity
                self._verify_data_file()
        except Exception as e:
            logger.error(f"Error ensuring data file: {e}")
            self._create_initial_data_file()
    
    def _create_initial_data_file(self):
        """Create initial data.json file with proper structure"""
        try:
            initial_data = {
                "metadata": {
                    "created": datetime.now().isoformat(),
                    "version": "1.0",
                    "total_qa_pairs": 0
                },
                "qa_pairs": {}
            }
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Created initial data file: {self.data_file}")
            
        except Exception as e:
            logger.error(f"Error creating initial data file: {e}")
    
    def _verify_data_file(self):
        """Verify data file integrity and fix if needed"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check required structure
            if not isinstance(data, dict):
                raise ValueError("Data file is not a valid JSON object")
            
            if "qa_pairs" not in data:
                data["qa_pairs"] = {}
            
            if "metadata" not in data:
                data["metadata"] = {
                    "created": datetime.now().isoformat(),
                    "version": "1.0",
                    "total_qa_pairs": len(data.get("qa_pairs", {}))
                }
            
            # Save corrected structure
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Data file corrupted, recreating: {e}")
            self._create_initial_data_file()
        except Exception as e:
            logger.error(f"Error verifying data file: {e}")
            self._create_initial_data_file()
    
    def _load_data(self) -> Dict[str, Any]:
        """Safely load data from file"""
        try:
            if not os.path.exists(self.data_file):
                self._create_initial_data_file()
            
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error, recreating file: {e}")
            self._create_initial_data_file()
            return self._load_data()
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return {"metadata": {}, "qa_pairs": {}}
    
    def _save_data(self, data: Dict[str, Any]):
        """Safely save data to file"""
        try:
            # Update metadata
            data["metadata"]["last_updated"] = datetime.now().isoformat()
            data["metadata"]["total_qa_pairs"] = len(data.get("qa_pairs", {}))
            
            # Write to temporary file first
            temp_file = f"{self.data_file}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Replace original file
            os.replace(temp_file, self.data_file)
            
        except Exception as e:
            logger.error(f"Error saving data: {e}")
            # Clean up temp file if it exists
            try:
                if os.path.exists(f"{self.data_file}.tmp"):
                    os.remove(f"{self.data_file}.tmp")
            except:
                pass
    
    def _normalize_question(self, question: str) -> str:
        """Normalize question for better matching"""
        # Remove extra whitespace and convert to lowercase
        normalized = ' '.join(question.strip().split()).lower()
        
        # Remove common punctuation that doesn't affect meaning
        import re
        normalized = re.sub(r'[.,!?;:()]+$', '', normalized)
        
        return normalized
    
    def get_cached_response(self, question: str) -> Optional[str]:
        """Get cached response for a question - disabled for natural conversations"""
        # Disable caching to ensure fresh GPT responses for natural conversations
        return None
    
    def _find_similar_question(self, question: str, qa_pairs: Dict[str, Any]) -> Optional[str]:
        """Find similar questions using simple similarity matching"""
        try:
            from difflib import SequenceMatcher
            
            best_match = None
            best_ratio = 0.85  # Minimum similarity threshold
            
            for cached_question, response_data in qa_pairs.items():
                similarity = SequenceMatcher(None, question, cached_question).ratio()
                
                if similarity > best_ratio:
                    best_ratio = similarity
                    if isinstance(response_data, dict):
                        best_match = response_data.get("answer")
                    else:
                        best_match = response_data
            
            return best_match
            
        except Exception as e:
            logger.error(f"Error in similarity matching: {e}")
            return None
    
    def save_qa_pair(self, question: str, answer: str):
        """Save a new question-answer pair"""
        with self.lock:
            try:
                data = self._load_data()
                qa_pairs = data.get("qa_pairs", {})
                
                normalized_question = self._normalize_question(question)
                
                # Store with metadata
                qa_pairs[normalized_question] = {
                    "question": question,  # Original question
                    "answer": answer,
                    "created": datetime.now().isoformat(),
                    "usage_count": 1
                }
                
                data["qa_pairs"] = qa_pairs
                self._save_data(data)
                
                logger.info(f"Saved Q&A pair: {question[:50]}...")
                
            except Exception as e:
                logger.error(f"Error saving Q&A pair: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the data"""
        try:
            data = self._load_data()
            qa_pairs = data.get("qa_pairs", {})
            
            return {
                "total_qa_pairs": len(qa_pairs),
                "file_size": os.path.getsize(self.data_file) if os.path.exists(self.data_file) else 0,
                "created": data.get("metadata", {}).get("created", "Unknown"),
                "last_updated": data.get("metadata", {}).get("last_updated", "Never")
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
    
    def clear_cache(self):
        """Clear all cached data"""
        with self.lock:
            try:
                self._create_initial_data_file()
                logger.info("Cleared all cached data")
            except Exception as e:
                logger.error(f"Error clearing cache: {e}")
