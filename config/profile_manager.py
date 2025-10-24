"""
Profile Manager - Load and manage user profiles for job search.
"""

import json
from pathlib import Path
from typing import Optional
from models.user_profile import UserProfile


class ProfileManager:
    """Manages user profiles for job search configuration."""

    def __init__(self, profiles_dir: Optional[Path] = None):
        """
        Initialize ProfileManager.

        Args:
            profiles_dir: Directory containing profile JSON files.
                         Defaults to project_root/profiles
        """
        if profiles_dir is None:
            # Default to profiles directory in project root
            base_dir = Path(__file__).parent.parent
            profiles_dir = base_dir / "profiles"

        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    def load_profile(self, profile_id: str) -> UserProfile:
        """
        Load a user profile by ID.

        Args:
            profile_id: Profile identifier (filename without .json)

        Returns:
            UserProfile instance

        Raises:
            FileNotFoundError: If profile file doesn't exist
            ValueError: If profile JSON is invalid
        """
        profile_path = self.profiles_dir / f"{profile_id}.json"

        if not profile_path.exists():
            raise FileNotFoundError(
                f"Profile '{profile_id}' not found at {profile_path}. "
                f"Available profiles: {self.list_profiles()}"
            )

        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)

            # Ensure profile_id is set
            if 'profile_id' not in profile_data:
                profile_data['profile_id'] = profile_id

            return UserProfile(**profile_data)

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in profile '{profile_id}': {e}")
        except Exception as e:
            raise ValueError(f"Error loading profile '{profile_id}': {e}")

    def save_profile(self, profile: UserProfile, profile_id: Optional[str] = None) -> Path:
        """
        Save a user profile to JSON file.

        Args:
            profile: UserProfile instance to save
            profile_id: Optional profile ID override. If not provided, uses profile.profile_id

        Returns:
            Path to saved profile file

        Raises:
            ValueError: If no profile_id is available
        """
        pid = profile_id or profile.profile_id
        if not pid:
            raise ValueError("profile_id must be provided either in profile or as parameter")

        profile_path = self.profiles_dir / f"{pid}.json"

        # Update profile_id if needed
        if profile.profile_id != pid:
            profile.profile_id = pid

        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(profile.model_dump(), f, indent=2, ensure_ascii=False)

        print(f"✅ Profile saved to {profile_path}")
        return profile_path

    def list_profiles(self) -> list[str]:
        """
        List all available profile IDs.

        Returns:
            List of profile IDs (filenames without .json extension)
        """
        json_files = self.profiles_dir.glob("*.json")
        return sorted([f.stem for f in json_files])

    def profile_exists(self, profile_id: str) -> bool:
        """
        Check if a profile exists.

        Args:
            profile_id: Profile identifier

        Returns:
            True if profile exists, False otherwise
        """
        profile_path = self.profiles_dir / f"{profile_id}.json"
        return profile_path.exists()

    def get_default_profile(self) -> UserProfile:
        """
        Get default profile. Tries to load 'default.json', falls back to first available.

        Returns:
            UserProfile instance

        Raises:
            FileNotFoundError: If no profiles exist
        """
        # Try to load 'default' profile
        if self.profile_exists('default'):
            return self.load_profile('default')

        # Fall back to first available profile
        available = self.list_profiles()
        if not available:
            raise FileNotFoundError(
                f"No profiles found in {self.profiles_dir}. "
                "Please create a profile first."
            )

        print(f"⚠️  No 'default' profile found, using '{available[0]}'")
        return self.load_profile(available[0])


# Singleton instance for easy access
_profile_manager = None


def get_profile_manager(profiles_dir: Optional[Path] = None) -> ProfileManager:
    """
    Get or create ProfileManager singleton.

    Args:
        profiles_dir: Optional directory for profiles

    Returns:
        ProfileManager instance
    """
    global _profile_manager
    if _profile_manager is None:
        _profile_manager = ProfileManager(profiles_dir)
    return _profile_manager
