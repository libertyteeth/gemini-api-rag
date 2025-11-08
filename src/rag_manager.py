"""RAG manager using Gemini File Search."""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional

import google.generativeai as genai


class RAGManager:
    """Manage Gemini File Search for RAG operations."""

    def __init__(self, config_dir: str = 'config'):
        """
        Initialize RAG manager.

        Args:
            config_dir: Directory to store configuration
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / 'store_config.json'
        self.config = self._load_config()
        self.file_search_store = None

    def _load_config(self) -> Dict:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Could not load {self.config_file}, starting fresh")
                return {}
        return {}

    def _save_config(self):
        """Save configuration to file."""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, indent=2, fp=f)

    def create_or_get_store(self, store_name: str = 'youtube_transcripts') -> str:
        """
        Create a new File Search store or get existing one.

        Args:
            store_name: Name for the vector store

        Returns:
            Store name/ID
        """
        # Check if we already have a store configured
        if store_name in self.config:
            store_id = self.config[store_name]['store_id']
            print(f"Using existing store: {store_id}")
            try:
                # Verify the store still exists
                self.file_search_store = genai.get_file_search_store(store_id)
                return store_id
            except Exception as e:
                print(f"Stored vector store not found, creating new one: {e}")

        # Create new store
        print(f"Creating new File Search store: {store_name}")
        try:
            # Note: The actual API may differ slightly - this is based on the docs
            # You might need to adjust based on the actual SDK implementation
            self.file_search_store = genai.create_file_search_store(
                display_name=store_name
            )

            store_id = self.file_search_store.name

            # Save configuration
            self.config[store_name] = {
                'store_id': store_id,
                'display_name': store_name,
                'created_at': time.time(),
            }
            self._save_config()

            print(f"✓ Created store: {store_id}")
            return store_id

        except Exception as e:
            print(f"Error creating File Search store: {e}")
            print("Note: File Search API might need specific setup or API access")
            raise

    def upload_files(
        self, file_paths: List[Path], store_name: str = 'youtube_transcripts'
    ) -> Dict:
        """
        Upload transcript files to the File Search store.

        Args:
            file_paths: List of file paths to upload
            store_name: Name of the vector store

        Returns:
            Dictionary with upload results
        """
        store_id = self.create_or_get_store(store_name)

        uploaded_files = []
        total_tokens = 0
        errors = []

        print(f"\n{'=' * 80}")
        print(f"UPLOADING FILES TO VECTOR STORE")
        print(f"{'=' * 80}")

        for i, filepath in enumerate(file_paths, 1):
            print(f"\n[{i}/{len(file_paths)}] Uploading: {filepath.name}")

            try:
                # Upload and import file to store
                # Note: API syntax based on documentation, may need adjustment
                operation = genai.upload_to_file_search_store(
                    file=str(filepath),
                    file_search_store_name=store_id,
                )

                # Estimate tokens (rough: file size / 4)
                file_size = filepath.stat().st_size
                estimated_tokens = file_size // 4

                uploaded_files.append({
                    'filepath': str(filepath),
                    'filename': filepath.name,
                    'estimated_tokens': estimated_tokens,
                })

                total_tokens += estimated_tokens
                print(f"  ✓ Uploaded successfully")
                print(f"  ✓ Estimated tokens: {estimated_tokens:,}")

            except Exception as e:
                error_msg = f"Failed to upload {filepath.name}: {e}"
                print(f"  ✗ {error_msg}")
                errors.append(error_msg)

        print(f"\n{'=' * 80}")
        print(f"UPLOAD COMPLETE")
        print(f"{'=' * 80}")
        print(f"Files uploaded: {len(uploaded_files)}/{len(file_paths)}")
        print(f"Total estimated tokens: {total_tokens:,}")
        if errors:
            print(f"Errors: {len(errors)}")
        print(f"{'=' * 80}\n")

        return {
            'store_id': store_id,
            'uploaded_count': len(uploaded_files),
            'total_files': len(file_paths),
            'total_tokens': total_tokens,
            'files': uploaded_files,
            'errors': errors,
        }

    def query(
        self,
        prompt: str,
        store_name: str = 'youtube_transcripts',
        model_name: str = 'gemini-2.0-flash-exp',
    ) -> Dict:
        """
        Query the RAG system.

        Args:
            prompt: User's query
            store_name: Name of the vector store
            model_name: Model to use for generation

        Returns:
            Dictionary with response and metadata
        """
        store_id = self.create_or_get_store(store_name)

        print(f"Querying: {prompt[:100]}...")

        try:
            # Create model with File Search tool
            # Note: API syntax based on documentation, may need adjustment
            model = genai.GenerativeModel(model_name)

            # Configure with File Search tool
            config = {
                'tools': [
                    {
                        'file_search': {
                            'file_search_store_names': [store_id]
                        }
                    }
                ]
            }

            # Generate response
            response = model.generate_content(
                prompt,
                generation_config=config,
            )

            # Extract response text
            response_text = response.text

            # Get token counts
            try:
                input_tokens = response.usage_metadata.prompt_token_count
                output_tokens = response.usage_metadata.candidates_token_count
            except AttributeError:
                # Fallback if usage metadata not available
                input_tokens = 0
                output_tokens = 0

            # Get grounding metadata (citations)
            grounding_metadata = None
            try:
                if hasattr(response, 'grounding_metadata'):
                    grounding_metadata = response.grounding_metadata
            except Exception:
                pass

            return {
                'prompt': prompt,
                'response': response_text,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'model': model_name,
                'grounding_metadata': grounding_metadata,
            }

        except Exception as e:
            print(f"Error querying RAG: {e}")
            raise

    def list_files_in_store(self, store_name: str = 'youtube_transcripts') -> List:
        """
        List files in the vector store.

        Args:
            store_name: Name of the vector store

        Returns:
            List of files in the store
        """
        try:
            store_id = self.create_or_get_store(store_name)
            # Note: API for listing files may vary
            # This is a placeholder - adjust based on actual API
            files = genai.list_files_in_store(store_id)
            return list(files)
        except Exception as e:
            print(f"Error listing files: {e}")
            return []

    def delete_store(self, store_name: str = 'youtube_transcripts'):
        """
        Delete a File Search store.

        Args:
            store_name: Name of the vector store to delete
        """
        if store_name not in self.config:
            print(f"Store '{store_name}' not found in configuration")
            return

        store_id = self.config[store_name]['store_id']

        try:
            genai.delete_file_search_store(store_id)
            del self.config[store_name]
            self._save_config()
            print(f"✓ Deleted store: {store_name}")
        except Exception as e:
            print(f"Error deleting store: {e}")

    def get_store_info(self, store_name: str = 'youtube_transcripts') -> Optional[Dict]:
        """
        Get information about a store.

        Args:
            store_name: Name of the vector store

        Returns:
            Store information or None
        """
        return self.config.get(store_name)
