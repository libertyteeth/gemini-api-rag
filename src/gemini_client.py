"""Gemini API client with authentication support."""

import os
import subprocess
import sys
from typing import Optional

import google.generativeai as genai


class GeminiClient:
    """Handles Gemini API authentication and client initialization."""

    def __init__(self):
        """Initialize the Gemini client with API key or gcloud CLI."""
        self.api_key: Optional[str] = None
        self.authenticated = False
        self.auth_method = None

    def authenticate(self) -> bool:
        """
        Authenticate with Gemini API.

        Priority:
        1. Try GEMINI_API_KEY environment variable
        2. Fall back to gcloud CLI authentication

        Returns:
            bool: True if authentication successful

        Raises:
            RuntimeError: If all authentication methods fail
        """
        # Try API key first
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            try:
                # Configure with API key for Google AI Studio
                # Note: This uses ai.google.dev endpoint, not cloud.google.com
                genai.configure(api_key=api_key)
                self.api_key = api_key
                self.auth_method = "API_KEY"

                # Verify the API key works
                if self._verify_connection():
                    self.authenticated = True
                    print("✓ Authenticated using GEMINI_API_KEY")
                    return True
                else:
                    print("✗ GEMINI_API_KEY found but invalid")
            except Exception as e:
                print(f"✗ Failed to authenticate with API key: {e}")

        # Fall back to gcloud CLI
        print("Attempting gcloud CLI authentication...")
        if self._authenticate_with_gcloud():
            self.authenticated = True
            self.auth_method = "GCLOUD_CLI"
            print("✓ Authenticated using gcloud CLI")
            return True

        raise RuntimeError(
            "Authentication failed. Please either:\n"
            "1. Set GEMINI_API_KEY environment variable, or\n"
            "2. Configure gcloud CLI with: gcloud auth application-default login"
        )

    def _authenticate_with_gcloud(self) -> bool:
        """
        Authenticate using gcloud CLI with Application Default Credentials.

        For gcloud authentication, the google-generativeai library automatically
        picks up Application Default Credentials. We just need to verify they exist.

        Returns:
            bool: True if authentication successful
        """
        try:
            # Check if gcloud is installed
            result = subprocess.run(
                ['gcloud', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                print("✗ gcloud CLI not found")
                return False

            # Check if application default credentials are configured
            result = subprocess.run(
                ['gcloud', 'auth', 'application-default', 'print-access-token'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                print("✗ gcloud application default credentials not configured")
                print("  Run: gcloud auth application-default login")
                return False

            # Don't configure genai - it will automatically pick up ADC
            # Just verify the connection works
            if self._verify_connection():
                return True
            else:
                print("✗ gcloud credentials found but API connection failed")
                print("  Note: Ensure you're using a Google Cloud project with Gemini API enabled")
                return False

        except subprocess.TimeoutExpired:
            print("✗ gcloud command timed out")
            return False
        except FileNotFoundError:
            print("✗ gcloud CLI not installed")
            return False
        except Exception as e:
            print(f"✗ gcloud authentication error: {e}")
            return False

    def _verify_connection(self) -> bool:
        """
        Verify API connectivity by listing models.

        Returns:
            bool: True if connection successful
        """
        try:
            # Try to list models as a connectivity check
            models = list(genai.list_models())
            return len(models) > 0
        except Exception as e:
            print(f"✗ API verification failed: {e}")
            return False

    def get_model(self, model_name: str = "gemini-2.0-flash-exp"):
        """
        Get a Gemini model instance.

        Args:
            model_name: Name of the model to use

        Returns:
            GenerativeModel instance

        Raises:
            RuntimeError: If not authenticated
        """
        if not self.authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        return genai.GenerativeModel(model_name)

    def list_available_models(self) -> list:
        """
        List available Gemini models.

        Returns:
            List of model names
        """
        if not self.authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        try:
            models = genai.list_models()
            return [model.name for model in models]
        except Exception as e:
            print(f"Error listing models: {e}")
            return []
