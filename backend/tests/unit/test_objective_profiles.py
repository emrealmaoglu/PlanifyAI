"""
Unit Tests for Objective Profiles
==================================

Tests for objective_profiles.py module.

Created: 2026-01-03
"""

import pytest

from src.algorithms import (
    ObjectiveProfile,
    ProfileType,
    create_custom_profile,
    get_profile,
    list_available_profiles,
)


class TestObjectiveProfile:
    """Test ObjectiveProfile dataclass."""

    def test_valid_profile(self):
        """Test creating valid profile."""
        profile = ObjectiveProfile(
            name="Test",
            use_enhanced=True,
            weights={"cost": 0.25, "walking": 0.25, "adjacency": 0.25, "diversity": 0.25},
            walking_speed_kmh=5.0,
            description="Test profile",
        )

        assert profile.name == "Test"
        assert profile.use_enhanced is True
        assert len(profile.weights) == 4
        assert sum(profile.weights.values()) == pytest.approx(1.0)

    def test_invalid_weights_sum(self):
        """Test that weights must sum to 1.0."""
        with pytest.raises(ValueError, match="Weights must sum to 1.0"):
            ObjectiveProfile(
                name="Invalid",
                use_enhanced=False,
                weights={"cost": 0.5, "walking": 0.3, "adjacency": 0.1},  # Sums to 0.9
            )

    def test_to_dict(self):
        """Test serialization to dict."""
        profile = ObjectiveProfile(
            name="Test",
            use_enhanced=True,
            weights={"cost": 0.33, "walking": 0.34, "adjacency": 0.33},
            walking_speed_kmh=4.0,
            description="Test",
        )

        data = profile.to_dict()

        assert data["name"] == "Test"
        assert data["use_enhanced"] is True
        assert data["walking_speed_kmh"] == 4.0
        assert "weights" in data

    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "name": "Test",
            "use_enhanced": False,
            "weights": {"cost": 0.33, "walking": 0.34, "adjacency": 0.33},
            "walking_speed_kmh": 5.0,
            "description": "Test",
        }

        profile = ObjectiveProfile.from_dict(data)

        assert profile.name == "Test"
        assert profile.use_enhanced is False
        assert profile.walking_speed_kmh == 5.0


class TestPredefinedProfiles:
    """Test predefined profile functions."""

    def test_get_standard_profile(self):
        """Test standard profile."""
        profile = get_profile(ProfileType.STANDARD)

        assert profile.name == "Standard"
        assert profile.use_enhanced is False
        assert len(profile.weights) == 3
        assert "cost" in profile.weights
        assert "walking" in profile.weights
        assert "adjacency" in profile.weights
        assert sum(profile.weights.values()) == pytest.approx(1.0)

    def test_get_research_enhanced_profile(self):
        """Test research-enhanced profile."""
        profile = get_profile(ProfileType.RESEARCH_ENHANCED)

        assert profile.name == "Research-Enhanced"
        assert profile.use_enhanced is True
        assert len(profile.weights) == 4
        assert "diversity" in profile.weights
        assert sum(profile.weights.values()) == pytest.approx(1.0)

    def test_get_fifteen_minute_city_profile(self):
        """Test 15-minute city profile."""
        profile = get_profile(ProfileType.FIFTEEN_MINUTE_CITY)

        assert profile.name == "15-Minute City"
        assert profile.use_enhanced is True
        assert profile.weights["walking"] == 0.50  # 50% weight on accessibility
        assert profile.walking_speed_kmh == 3.0  # Elderly speed
        assert sum(profile.weights.values()) == pytest.approx(1.0)

    def test_get_campus_planning_profile(self):
        """Test campus planning profile."""
        profile = get_profile(ProfileType.CAMPUS_PLANNING)

        assert profile.name == "Campus Planning"
        assert profile.use_enhanced is True
        assert profile.weights["adjacency"] == 0.50  # 50% weight on adjacency
        assert profile.walking_speed_kmh == 5.0  # Healthy speed
        assert sum(profile.weights.values()) == pytest.approx(1.0)

    def test_get_custom_profile_raises(self):
        """Test that getting CUSTOM profile raises error."""
        with pytest.raises(ValueError, match="Use create_custom_profile"):
            get_profile(ProfileType.CUSTOM)


class TestCustomProfile:
    """Test custom profile creation."""

    def test_create_custom_profile(self):
        """Test creating custom profile."""
        profile = create_custom_profile(
            name="My Custom",
            use_enhanced=True,
            weights={"cost": 0.3, "walking": 0.3, "adjacency": 0.2, "diversity": 0.2},
            walking_speed_kmh=4.5,
            description="Custom test profile",
        )

        assert profile.name == "My Custom"
        assert profile.use_enhanced is True
        assert profile.walking_speed_kmh == 4.5
        assert profile.description == "Custom test profile"
        assert sum(profile.weights.values()) == pytest.approx(1.0)

    def test_create_custom_invalid_weights(self):
        """Test custom profile with invalid weights."""
        with pytest.raises(ValueError, match="Weights must sum to 1.0"):
            create_custom_profile(
                name="Invalid",
                use_enhanced=False,
                weights={"cost": 0.5, "walking": 0.5, "adjacency": 0.5},  # Sums to 1.5
            )


class TestListProfiles:
    """Test listing available profiles."""

    def test_list_available_profiles(self):
        """Test listing all profiles."""
        profiles = list_available_profiles()

        assert isinstance(profiles, dict)
        assert len(profiles) >= 4  # At least 4 predefined profiles
        assert "Standard" in profiles
        assert "Research-Enhanced" in profiles
        assert "15-Minute City" in profiles
        assert "Campus Planning" in profiles

        # Check descriptions exist
        for name, desc in profiles.items():
            assert isinstance(desc, str)
            assert len(desc) > 0


class TestProfileTypeEnum:
    """Test ProfileType enum."""

    def test_profile_type_values(self):
        """Test ProfileType enum values."""
        assert ProfileType.STANDARD.value == "standard"
        assert ProfileType.RESEARCH_ENHANCED.value == "research_enhanced"
        assert ProfileType.FIFTEEN_MINUTE_CITY.value == "15_minute_city"
        assert ProfileType.CAMPUS_PLANNING.value == "campus_planning"
        assert ProfileType.CUSTOM.value == "custom"

    def test_profile_type_from_string(self):
        """Test creating ProfileType from string."""
        assert ProfileType("standard") == ProfileType.STANDARD
        assert ProfileType("research_enhanced") == ProfileType.RESEARCH_ENHANCED
        assert ProfileType("15_minute_city") == ProfileType.FIFTEEN_MINUTE_CITY


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
