"""
Basic tests for Healthcare Eligibility Pipeline
"""

import pytest
import pandas as pd
from pathlib import Path
import sys
import tempfile
import yaml

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from eligibility_pipeline import EligibilityPipeline


@pytest.fixture
def sample_config():
    """Create a sample configuration for testing."""
    return {
        'partners': {
            'test_partner': {
                'partner_code': 'TEST',
                'file_path': 'data/test.csv',
                'delimiter': ',',
                'date_format': '%Y-%m-%d',
                'column_mapping': {
                    'external_id': 'id',
                    'first_name': 'fname',
                    'last_name': 'lname',
                    'dob': 'birth_date',
                    'email': 'email',
                    'phone': 'phone'
                }
            }
        }
    }


@pytest.fixture
def temp_config_file(sample_config):
    """Create a temporary config file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(sample_config, f)
        return f.name


@pytest.fixture
def pipeline(temp_config_file):
    """Create a pipeline instance for testing."""
    return EligibilityPipeline(temp_config_file)


class TestPhoneFormatting:
    """Test phone number formatting."""
    
    def test_format_phone_standard(self, pipeline):
        """Test standard 10-digit phone number."""
        result = pipeline._format_phone('5551234567')
        assert result == '555-123-4567'
    
    def test_format_phone_with_dashes(self, pipeline):
        """Test phone number already formatted."""
        result = pipeline._format_phone('555-123-4567')
        assert result == '555-123-4567'
    
    def test_format_phone_null(self, pipeline):
        """Test null phone number."""
        result = pipeline._format_phone(None)
        assert result is None


class TestDateFormatting:
    """Test date formatting."""
    
    def test_format_date_iso(self, pipeline):
        """Test ISO date format."""
        result = pipeline._format_date('1955-03-15', '%Y-%m-%d')
        assert result == '1955-03-15'
    
    def test_format_date_us_format(self, pipeline):
        """Test US date format conversion."""
        result = pipeline._format_date('03/15/1955', '%m/%d/%Y')
        assert result == '1955-03-15'
    
    def test_format_date_null(self, pipeline):
        """Test null date."""
        result = pipeline._format_date(None, '%Y-%m-%d')
        assert result is None


class TestRowValidation:
    """Test row validation logic."""
    
    def test_validate_row_valid(self, pipeline):
        """Test validation of valid row."""
        row = {
            'external_id': 'TEST123',
            'first_name': 'John',
            'last_name': 'Doe',
            'dob': '1955-03-15',
            'email': 'john.doe@email.com',
            'phone': '555-123-4567',
            'partner_code': 'TEST'
        }
        assert pipeline._validate_row(row) is True
    
    def test_validate_row_missing_id(self, pipeline):
        """Test validation when external_id is missing."""
        row = {
            'external_id': None,
            'first_name': 'John',
            'last_name': 'Doe',
            'dob': '1955-03-15',
            'email': 'john.doe@email.com',
            'phone': '555-123-4567',
            'partner_code': 'TEST'
        }
        assert pipeline._validate_row(row) is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])