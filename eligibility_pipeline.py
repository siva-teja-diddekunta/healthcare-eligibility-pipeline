"""
Healthcare Eligibility Data Pipeline
A configuration driven ETL pipeline for ingesting partner eligibility files
Author: Sivateja - January 2025
"""
import pandas as pd
import yaml
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class EligibilityPipeline:
    """
    Configuration-driven pipeline for processing healthcare eligibility data
    from multiple partners with varying file formats.
    """
    
    def __init__(self, config_path: str):
        """Initialize pipeline with configuration file."""
        self.config_file = Path(config_path)
        self.partners_config = self._load_config()
        self.output_columns = [
            'external_id', 'first_name', 'last_name', 
            'dob', 'email', 'phone', 'partner_code'
        ]
    
    def _load_config(self) -> Dict:
        """Load and validate configuration from YAML file."""
        try:
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            if 'partners' not in config:
                raise ValueError("Config missing 'partners' section")
            
            logger.info(f"Configuration loaded: {len(config['partners'])} partners")
            return config
            
        except FileNotFoundError:
            logger.error(f"Config file not found: {self.config_file}")
            raise
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise
    
    def _read_partner_file(self, partner_config: Dict) -> pd.DataFrame:
        """Read partner file based on configuration."""
        file_path = partner_config['file_path']
        delimiter = partner_config['delimiter']
        
        try:
            df = pd.read_csv(file_path, delimiter=delimiter)
            logger.info(f"Read {len(df)} rows from {file_path}")
            return df
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise
    
    def _format_phone(self, phone: str) -> str:
        """Format phone number to XXX-XXX-XXXX."""
        if pd.isna(phone):
            return None
        
        # Extract only digits
        digits = re.sub(r'\D', '', str(phone))
        
        # Format as XXX-XXX-XXXX if 10 digits
        if len(digits) == 10:
            return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
        else:
            logger.warning(f"Non-standard phone format: {phone}")
            return digits
    
    def _format_date(self, date_str: str, input_format: str) -> Optional[str]:
        """Convert date to ISO-8601 format (YYYY-MM-DD)."""
        if pd.isna(date_str):
            return None
        
        try:
            date_obj = datetime.strptime(str(date_str), input_format)
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            logger.warning(f"Invalid date format: {date_str}")
            return None
    
    def _transform_row(self, row: pd.Series, partner_config: Dict) -> Dict:
        """Transform a single row to standardized format."""
        mapping = partner_config['column_mapping']
        
        transformed = {
            'external_id': row.get(mapping['external_id']),
            'first_name': str(row.get(mapping['first_name'], '')).strip().title(),
            'last_name': str(row.get(mapping['last_name'], '')).strip().title(),
            'dob': self._format_date(
                row.get(mapping['dob']), 
                partner_config.get('date_format', '%Y-%m-%d')
            ),
            'email': str(row.get(mapping['email'], '')).lower().strip(),
            'phone': self._format_phone(row.get(mapping['phone'])),
            'partner_code': partner_config['partner_code']
        }
        
        return transformed
    
    def _validate_row(self, row: Dict) -> bool:
        """Validate that row meets minimum requirements."""
        # Check if external_id is present
        if not row.get('external_id') or pd.isna(row.get('external_id')):
            logger.warning(f"Row missing external_id, excluding from output")
            return False
        
        # Check if date of birth is valid
        if not row.get('dob'):
            logger.warning(f"Invalid DOB for ID: {row.get('external_id')}, excluding")
            return False
        
        return True
    
    def process_partner(self, partner_name: str) -> pd.DataFrame:
        """Process a single partner's data."""
        logger.info(f"Processing partner: {partner_name}")
        
        partner_config = self.partners_config['partners'][partner_name]
        
        # Read raw data
        raw_df = self._read_partner_file(partner_config)
        
        # Transform and validate each row
        transformed_rows = []
        invalid_count = 0
        
        for idx, row in raw_df.iterrows():
            try:
                transformed = self._transform_row(row, partner_config)
                
                if self._validate_row(transformed):
                    transformed_rows.append(transformed)
                else:
                    invalid_count += 1
                    
            except Exception as e:
                logger.error(f"Error processing row {idx}: {e}")
                invalid_count += 1
        
        logger.info(f"Partner {partner_name}: {len(transformed_rows)} valid, {invalid_count} invalid")
        
        return pd.DataFrame(transformed_rows, columns=self.output_columns)
    
    def run(self, output_path: str = 'output/unified_eligibility.csv') -> pd.DataFrame:
        """Execute the full pipeline for all configured partners."""
        logger.info("="*60)
        logger.info("Starting eligibility pipeline")
        logger.info("="*60)
        
        all_data = []
        
        # Process each partner
        for partner_name in self.partners_config['partners'].keys():
            try:
                partner_df = self.process_partner(partner_name)
                all_data.append(partner_df)
            except Exception as e:
                logger.error(f"Failed to process partner {partner_name}: {e}")
                continue
        
        if not all_data:
            logger.error("No data was successfully processed")
            return pd.DataFrame(columns=self.output_columns)
        
        # Combine all partner data
        unified_df = pd.concat(all_data, ignore_index=True)
        
        logger.info(f"Pipeline complete: {len(unified_df)} total records")
        
        # Save output
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        unified_df.to_csv(output_file, index=False)
        logger.info(f"Output saved to: {output_file}")
        
        return unified_df


def main():
    """Main execution function."""
    print("\n" + "="*60)
    print("Healthcare Eligibility Pipeline")
    print("="*60 + "\n")
    
    # Initialize and run pipeline
    pipeline = EligibilityPipeline('config/partners.yaml')
    result_df = pipeline.run()
    
    # Display summary
    print("\n" + "="*60)
    print("EXECUTION SUMMARY")
    print("="*60)
    print(f"Total Records Processed: {len(result_df)}")
    print(f"\nRecords by Partner:")
    print(result_df['partner_code'].value_counts())
    print("\n" + "="*60)
    print("Sample Output (first 5 rows):")
    print(result_df.head())
    print("\n" + "="*60)
    print("Pipeline completed successfully!")
    print(f"Output saved to: output/unified_eligibility.csv")
    print("="*60 + "\n")
    

if __name__ == "__main__":
    main()