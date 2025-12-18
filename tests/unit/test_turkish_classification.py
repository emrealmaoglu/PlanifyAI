"""
Unit tests for Turkish building classification system
Target: 90%+ coverage
"""

import pytest
from backend.core.turkish_standards import (
    TurkishBuildingClassifier,
    BuildingClass,
    BuildingClassInfo,
)


class TestTurkishBuildingClassifier:
    """Test suite for building classification"""

    @pytest.fixture
    def classifier(self):
        """Fixture: classifier instance"""
        return TurkishBuildingClassifier()

    def test_classify_residential_low(self, classifier):
        """Test classification of low-rise residential"""
        result = classifier.classify("residential_low", 2000, 3)
        assert result == BuildingClass.CLASS_III_A

    def test_classify_residential_mid(self, classifier):
        """Test classification of mid-rise residential"""
        result = classifier.classify("residential_mid", 3000, 6)
        assert result == BuildingClass.CLASS_IV_B

    def test_classify_residential_high(self, classifier):
        """Test classification of high-rise residential"""
        result = classifier.classify("residential_high", 5000, 10)
        assert result == BuildingClass.CLASS_IV_B

    def test_classify_educational_university(self, classifier):
        """Test classification of university building"""
        result = classifier.classify("educational_university", 5000, 4)
        assert result == BuildingClass.CLASS_V_A

    def test_classify_educational_school(self, classifier):
        """Test classification of school"""
        result = classifier.classify("educational_school", 3000, 3)
        assert result == BuildingClass.CLASS_V_A

    def test_classify_educational_library(self, classifier):
        """Test classification of library"""
        result = classifier.classify("educational_library", 2000, 2)
        assert result == BuildingClass.CLASS_V_A

    def test_classify_health_hospital(self, classifier):
        """Test classification of hospital"""
        result = classifier.classify("health_hospital", 8000, 5)
        assert result == BuildingClass.CLASS_V_B

    def test_classify_health_clinic(self, classifier):
        """Test classification of clinic"""
        result = classifier.classify("health_clinic", 1000, 2)
        assert result == BuildingClass.CLASS_III_B

    def test_classify_commercial_retail(self, classifier):
        """Test classification of retail"""
        result = classifier.classify("commercial_retail", 500, 1)
        assert result == BuildingClass.CLASS_II_B

    def test_classify_commercial_mall(self, classifier):
        """Test classification of mall"""
        result = classifier.classify("commercial_mall", 10000, 3)
        assert result == BuildingClass.CLASS_IV_A

    def test_classify_commercial_office(self, classifier):
        """Test classification of office"""
        result = classifier.classify("commercial_office", 5000, 3)
        assert result == BuildingClass.CLASS_IV_A

    def test_classify_social_sports(self, classifier):
        """Test classification of sports facility"""
        result = classifier.classify("social_sports", 3000, 2)
        assert result == BuildingClass.CLASS_V_C

    def test_classify_social_cultural(self, classifier):
        """Test classification of cultural facility"""
        result = classifier.classify("social_cultural", 2000, 3)
        assert result == BuildingClass.CLASS_V_C

    def test_classify_social_recreation(self, classifier):
        """Test classification of recreation facility"""
        result = classifier.classify("social_recreation", 1500, 2)
        assert result == BuildingClass.CLASS_V_C

    def test_classify_administrative_office(self, classifier):
        """Test classification of administrative office"""
        result = classifier.classify("administrative_office", 4000, 3)
        assert result == BuildingClass.CLASS_IV_A

    def test_classify_administrative_municipal(self, classifier):
        """Test classification of municipal building"""
        result = classifier.classify("administrative_municipal", 1000, 1)
        assert result == BuildingClass.CLASS_II_B

    def test_classify_invalid_type(self, classifier):
        """Test error handling for invalid building type"""
        with pytest.raises(ValueError, match="Unknown building type"):
            classifier.classify("invalid_type", 1000, 2)

    def test_classify_empty_type(self, classifier):
        """Test error handling for empty building type"""
        with pytest.raises(ValueError, match="Unknown building type"):
            classifier.classify("", 1000, 2)

    def test_get_class_info(self, classifier):
        """Test retrieving class information"""
        info = classifier.get_class_info(BuildingClass.CLASS_V_A)
        assert isinstance(info, BuildingClassInfo)
        assert info.building_class == BuildingClass.CLASS_V_A
        assert info.cost_per_sqm_tl == 2000
        assert info.max_floors == 5

    def test_get_class_info_iii_a(self, classifier):
        """Test retrieving class information for III-A"""
        info = classifier.get_class_info(BuildingClass.CLASS_III_A)
        assert info.building_class == BuildingClass.CLASS_III_A
        assert info.cost_per_sqm_tl == 1500
        assert info.max_floors == 4
        assert "Konutlar" in info.name_tr

    def test_get_class_info_v_b(self, classifier):
        """Test retrieving class information for V-B"""
        info = classifier.get_class_info(BuildingClass.CLASS_V_B)
        assert info.building_class == BuildingClass.CLASS_V_B
        assert info.cost_per_sqm_tl == 2500
        assert info.max_floors == 6
        assert "Hastaneler" in info.name_tr

    def test_get_class_info_has_examples(self, classifier):
        """Test that class info includes examples"""
        info = classifier.get_class_info(BuildingClass.CLASS_V_A)
        assert isinstance(info.examples, list)
        assert len(info.examples) > 0

    def test_get_available_types(self, classifier):
        """Test listing available building types"""
        types = classifier.get_available_types()
        assert isinstance(types, list)
        assert len(types) > 10
        assert "residential_low" in types
        assert "educational_university" in types
        assert "health_hospital" in types

    def test_get_class_by_code_valid(self, classifier):
        """Test getting class from valid code"""
        result = classifier.get_class_by_code("V-A")
        assert result == BuildingClass.CLASS_V_A

    def test_get_class_by_code_iii_a(self, classifier):
        """Test getting class from III-A code"""
        result = classifier.get_class_by_code("III-A")
        assert result == BuildingClass.CLASS_III_A

    def test_get_class_by_code_iv_b(self, classifier):
        """Test getting class from IV-B code"""
        result = classifier.get_class_by_code("IV-B")
        assert result == BuildingClass.CLASS_IV_B

    def test_get_class_by_code_invalid(self, classifier):
        """Test getting class from invalid code"""
        result = classifier.get_class_by_code("INVALID")
        assert result is None

    def test_get_class_by_code_empty(self, classifier):
        """Test getting class from empty code"""
        result = classifier.get_class_by_code("")
        assert result is None

    def test_get_class_by_code_nonexistent(self, classifier):
        """Test getting class from nonexistent code"""
        result = classifier.get_class_by_code("X-Z")
        assert result is None

    @pytest.mark.parametrize(
        "building_type,expected_class",
        [
            ("residential_low", BuildingClass.CLASS_III_A),
            ("residential_mid", BuildingClass.CLASS_IV_B),
            ("residential_high", BuildingClass.CLASS_IV_B),
            ("commercial_office", BuildingClass.CLASS_IV_A),
            ("commercial_retail", BuildingClass.CLASS_II_B),
            ("educational_school", BuildingClass.CLASS_V_A),
            ("educational_university", BuildingClass.CLASS_V_A),
            ("health_clinic", BuildingClass.CLASS_III_B),
            ("health_hospital", BuildingClass.CLASS_V_B),
            ("social_sports", BuildingClass.CLASS_V_C),
        ],
    )
    def test_classify_multiple_types(self, classifier, building_type, expected_class):
        """Parametrized test for multiple building types"""
        result = classifier.classify(building_type, 3000, 3)
        assert result == expected_class

    @pytest.mark.parametrize(
        "class_code,expected_enum",
        [
            ("I-A", BuildingClass.CLASS_I_A),
            ("II-B", BuildingClass.CLASS_II_B),
            ("III-A", BuildingClass.CLASS_III_A),
            ("III-B", BuildingClass.CLASS_III_B),
            ("IV-A", BuildingClass.CLASS_IV_A),
            ("IV-B", BuildingClass.CLASS_IV_B),
            ("V-A", BuildingClass.CLASS_V_A),
            ("V-B", BuildingClass.CLASS_V_B),
            ("V-C", BuildingClass.CLASS_V_C),
        ],
    )
    def test_get_class_by_code_all_classes(self, classifier, class_code, expected_enum):
        """Parametrized test for all building classes"""
        result = classifier.get_class_by_code(class_code)
        assert result == expected_enum

    def test_classify_area_does_not_affect_class(self, classifier):
        """Test that area doesn't affect classification"""
        result1 = classifier.classify("residential_low", 1000, 3)
        result2 = classifier.classify("residential_low", 10000, 3)
        assert result1 == result2

    def test_classify_floors_does_not_affect_class(self, classifier):
        """Test that floors don't affect classification"""
        result1 = classifier.classify("residential_low", 2000, 1)
        result2 = classifier.classify("residential_low", 2000, 4)
        assert result1 == result2
