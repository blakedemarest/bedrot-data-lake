#!/usr/bin/env python3
"""
Data Integrity Checks Framework for BEDROT Data Lake
Validates data quality at zone boundaries, especially staging → curated promotion
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import json
import hashlib
from typing import Dict, List, Tuple, Optional, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataIntegrityChecker:
    """Comprehensive data integrity validation framework."""
    
    def __init__(self, dataset_name: str):
        self.dataset_name = dataset_name
        self.validation_results = {}
        self.error_details = []
        
    def validate_curated_promotion(self, df: pd.DataFrame, 
                                 schema: Optional[Dict[str, Any]] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Run comprehensive integrity checks before promoting data to curated zone.
        
        Args:
            df: DataFrame to validate
            schema: Optional schema definition for the dataset
            
        Returns:
            Tuple of (pass/fail, detailed results)
        """
        checks = {
            'row_count': self._check_row_count(df),
            'column_completeness': self._check_column_completeness(df, schema),
            'data_types': self._check_data_types(df, schema),
            'primary_key_uniqueness': self._check_primary_keys(df, schema),
            'date_continuity': self._check_date_continuity(df),
            'numeric_ranges': self._check_numeric_ranges(df, schema),
            'referential_integrity': self._check_referential_integrity(df, schema),
            'business_rules': self._check_business_rules(df),
            'data_freshness': self._check_data_freshness(df),
            'hash_consistency': self._check_hash_consistency(df)
        }
        
        # Calculate overall pass/fail
        all_passed = all(result['passed'] for result in checks.values())
        
        # Generate summary
        summary = {
            'dataset': self.dataset_name,
            'timestamp': datetime.now().isoformat(),
            'overall_passed': all_passed,
            'total_rows': len(df),
            'checks_performed': len(checks),
            'checks_passed': sum(1 for r in checks.values() if r['passed']),
            'checks_failed': sum(1 for r in checks.values() if not r['passed']),
            'validation_details': checks,
            'error_details': self.error_details
        }
        
        # Log results
        if all_passed:
            logger.info(f"✅ All integrity checks passed for {self.dataset_name}")
        else:
            logger.warning(f"❌ Integrity checks failed for {self.dataset_name}: "
                         f"{summary['checks_failed']} checks failed")
            
        return all_passed, summary
    
    def _check_row_count(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate row count is reasonable."""
        row_count = len(df)
        passed = row_count > 0
        
        if not passed:
            self.error_details.append("Dataset is empty")
            
        return {
            'passed': passed,
            'row_count': row_count,
            'message': f"Dataset contains {row_count} rows"
        }
    
    def _check_column_completeness(self, df: pd.DataFrame, 
                                  schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Check for required columns and null values."""
        results = {
            'passed': True,
            'missing_columns': [],
            'null_counts': {}
        }
        
        # Check required columns if schema provided
        if schema and 'required_columns' in schema:
            required = set(schema['required_columns'])
            actual = set(df.columns)
            missing = required - actual
            
            if missing:
                results['passed'] = False
                results['missing_columns'] = list(missing)
                self.error_details.append(f"Missing required columns: {missing}")
        
        # Check null values
        null_counts = df.isnull().sum()
        columns_with_nulls = null_counts[null_counts > 0].to_dict()
        
        if columns_with_nulls:
            # Determine if nulls are acceptable based on schema
            if schema and 'nullable_columns' in schema:
                nullable = set(schema['nullable_columns'])
                unexpected_nulls = set(columns_with_nulls.keys()) - nullable
                if unexpected_nulls:
                    results['passed'] = False
                    self.error_details.append(f"Unexpected nulls in: {unexpected_nulls}")
            
            results['null_counts'] = columns_with_nulls
            
        return results
    
    def _check_data_types(self, df: pd.DataFrame, 
                         schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Validate data types match expected schema."""
        results = {
            'passed': True,
            'type_mismatches': {}
        }
        
        if not schema or 'column_types' not in schema:
            # Basic type validation
            for col in df.columns:
                if 'date' in col.lower():
                    try:
                        pd.to_datetime(df[col])
                    except:
                        results['passed'] = False
                        results['type_mismatches'][col] = "Failed date parsing"
                        
        else:
            # Schema-based validation
            for col, expected_type in schema['column_types'].items():
                if col in df.columns:
                    actual_type = str(df[col].dtype)
                    if not self._types_compatible(actual_type, expected_type):
                        results['passed'] = False
                        results['type_mismatches'][col] = {
                            'expected': expected_type,
                            'actual': actual_type
                        }
                        
        return results
    
    def _check_primary_keys(self, df: pd.DataFrame, 
                           schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Check primary key uniqueness."""
        results = {
            'passed': True,
            'duplicate_count': 0,
            'duplicate_keys': []
        }
        
        if schema and 'primary_keys' in schema:
            pk_columns = schema['primary_keys']
            if all(col in df.columns for col in pk_columns):
                duplicates = df[df.duplicated(subset=pk_columns, keep=False)]
                
                if len(duplicates) > 0:
                    results['passed'] = False
                    results['duplicate_count'] = len(duplicates)
                    results['duplicate_keys'] = duplicates[pk_columns].drop_duplicates().head(10).to_dict('records')
                    self.error_details.append(f"Found {len(duplicates)} duplicate primary keys")
                    
        return results
    
    def _check_date_continuity(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check for gaps in date sequences."""
        results = {
            'passed': True,
            'date_gaps': [],
            'date_range': {}
        }
        
        # Find date columns
        date_cols = [col for col in df.columns if 'date' in col.lower()]
        
        for date_col in date_cols:
            try:
                dates = pd.to_datetime(df[date_col]).dropna()
                if len(dates) > 0:
                    date_range = {
                        'min': dates.min().strftime('%Y-%m-%d'),
                        'max': dates.max().strftime('%Y-%m-%d')
                    }
                    results['date_range'][date_col] = date_range
                    
                    # Check for gaps > 30 days
                    sorted_dates = dates.sort_values()
                    gaps = []
                    for i in range(1, len(sorted_dates)):
                        diff = (sorted_dates.iloc[i] - sorted_dates.iloc[i-1]).days
                        if diff > 30:
                            gaps.append({
                                'from': sorted_dates.iloc[i-1].strftime('%Y-%m-%d'),
                                'to': sorted_dates.iloc[i].strftime('%Y-%m-%d'),
                                'gap_days': diff
                            })
                    
                    if gaps:
                        results['date_gaps'] = gaps
                        # Don't fail for gaps, just warn
                        logger.warning(f"Date gaps found in {date_col}: {len(gaps)} gaps")
                        
            except Exception as e:
                logger.error(f"Error checking date continuity for {date_col}: {e}")
                
        return results
    
    def _check_numeric_ranges(self, df: pd.DataFrame, 
                            schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Validate numeric values are within expected ranges."""
        results = {
            'passed': True,
            'out_of_range': {}
        }
        
        # Common sense checks
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            # Check for negative values where inappropriate
            if any(term in col.lower() for term in ['count', 'views', 'streams', 'revenue']):
                negative_count = (df[col] < 0).sum()
                if negative_count > 0:
                    results['passed'] = False
                    results['out_of_range'][col] = f"{negative_count} negative values"
                    self.error_details.append(f"{col} has {negative_count} negative values")
            
            # Check for unrealistic values
            if 'revenue' in col.lower():
                # Revenue per stream shouldn't exceed $1
                if (df[col] > 1).any():
                    high_count = (df[col] > 1).sum()
                    results['out_of_range'][col] = f"{high_count} values > $1"
                    
        # Schema-based range checks
        if schema and 'numeric_ranges' in schema:
            for col, ranges in schema['numeric_ranges'].items():
                if col in df.columns:
                    min_val = ranges.get('min', -np.inf)
                    max_val = ranges.get('max', np.inf)
                    
                    out_of_range = df[(df[col] < min_val) | (df[col] > max_val)]
                    if len(out_of_range) > 0:
                        results['passed'] = False
                        results['out_of_range'][col] = f"{len(out_of_range)} values outside [{min_val}, {max_val}]"
                        
        return results
    
    def _check_referential_integrity(self, df: pd.DataFrame, 
                                   schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Check foreign key relationships."""
        results = {
            'passed': True,
            'invalid_references': {}
        }
        
        # Artist name validation
        if 'artist' in df.columns:
            valid_artists = {'pig1987', 'zone a0', 'zone_a0', 'zone.a0', 'PIG1987', 'ZONE A0', 'ZONE_A0'}
            invalid_artists = df[~df['artist'].str.lower().isin([a.lower() for a in valid_artists])]['artist'].unique()
            
            if len(invalid_artists) > 0:
                results['invalid_references']['artist'] = list(invalid_artists)
                logger.warning(f"Unknown artists found: {invalid_artists}")
                
        # Platform validation
        if 'platform' in df.columns:
            valid_platforms = {
                'spotify', 'apple music', 'tiktok', 'youtube', 'soundcloud',
                'amazon music', 'deezer', 'tidal', 'facebook', 'instagram'
            }
            invalid_platforms = df[~df['platform'].str.lower().isin(valid_platforms)]['platform'].unique()
            
            if len(invalid_platforms) > 0:
                results['invalid_references']['platform'] = list(invalid_platforms)
                
        return results
    
    def _check_business_rules(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Apply BEDROT-specific business rules."""
        results = {
            'passed': True,
            'rule_violations': []
        }
        
        # Rule 1: Streaming revenue should be ~$0.003 per stream
        if 'streams' in df.columns and 'revenue' in df.columns:
            df_filtered = df[(df['streams'] > 0) & (df['revenue'] > 0)]
            if len(df_filtered) > 0:
                revenue_per_stream = df_filtered['revenue'] / df_filtered['streams']
                
                # Check if revenue per stream is within reasonable range ($0.001 - $0.01)
                outliers = df_filtered[(revenue_per_stream < 0.001) | (revenue_per_stream > 0.01)]
                if len(outliers) > 0:
                    results['rule_violations'].append({
                        'rule': 'Revenue per stream out of range',
                        'count': len(outliers),
                        'details': f"Expected $0.001-0.01 per stream"
                    })
                    
        # Rule 2: TikTok engagement rate should be reasonable (0-100%)
        if all(col in df.columns for col in ['likes', 'comments', 'shares', 'video_views']):
            df_tiktok = df[df['video_views'] > 0].copy()
            if len(df_tiktok) > 0:
                engagement_rate = ((df_tiktok['likes'] + df_tiktok['comments'] + df_tiktok['shares']) / 
                                 df_tiktok['video_views'] * 100)
                
                high_engagement = df_tiktok[engagement_rate > 100]
                if len(high_engagement) > 0:
                    results['passed'] = False
                    results['rule_violations'].append({
                        'rule': 'TikTok engagement > 100%',
                        'count': len(high_engagement),
                        'details': "Engagement rate exceeds video views"
                    })
                    
        return results
    
    def _check_data_freshness(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check if data is recent enough."""
        results = {
            'passed': True,
            'staleness_days': None,
            'last_date': None
        }
        
        # Find the most recent date in the dataset
        date_cols = [col for col in df.columns if 'date' in col.lower()]
        
        if date_cols:
            most_recent = None
            for date_col in date_cols:
                try:
                    dates = pd.to_datetime(df[date_col]).dropna()
                    if len(dates) > 0:
                        col_max = dates.max()
                        if most_recent is None or col_max > most_recent:
                            most_recent = col_max
                except:
                    continue
                    
            if most_recent:
                staleness = (datetime.now() - most_recent).days
                results['staleness_days'] = staleness
                results['last_date'] = most_recent.strftime('%Y-%m-%d')
                
                # Fail if data is more than 7 days old
                if staleness > 7:
                    results['passed'] = False
                    self.error_details.append(f"Data is {staleness} days old")
                    
        return results
    
    def _check_hash_consistency(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate data hash for deduplication."""
        results = {
            'passed': True,
            'data_hash': None,
            'row_hashes': []
        }
        
        try:
            # Calculate overall dataframe hash
            df_string = df.to_csv(index=False, sort_index=True)
            data_hash = hashlib.sha256(df_string.encode()).hexdigest()[:16]
            results['data_hash'] = data_hash
            
            # Sample row hashes for verification
            if len(df) > 0:
                sample_size = min(5, len(df))
                for idx in df.head(sample_size).index:
                    row_string = df.loc[idx].to_json(sort_keys=True)
                    row_hash = hashlib.sha256(row_string.encode()).hexdigest()[:8]
                    results['row_hashes'].append(row_hash)
                    
        except Exception as e:
            logger.error(f"Error calculating hash: {e}")
            results['passed'] = False
            
        return results
    
    def _types_compatible(self, actual: str, expected: str) -> bool:
        """Check if actual and expected types are compatible."""
        type_mappings = {
            'int': ['int64', 'int32', 'int16', 'int8'],
            'float': ['float64', 'float32', 'float16'],
            'string': ['object', 'string'],
            'date': ['datetime64[ns]', 'datetime64'],
            'bool': ['bool', 'boolean']
        }
        
        for base_type, variants in type_mappings.items():
            if expected.lower() == base_type:
                return actual in variants
                
        return actual == expected

# Convenience function for cleaner scripts
def validate_before_curated_promotion(df: pd.DataFrame, dataset_name: str, 
                                    schema: Optional[Dict[str, Any]] = None) -> bool:
    """
    Quick validation function for use in cleaner scripts.
    
    Args:
        df: DataFrame to validate
        dataset_name: Name of the dataset
        schema: Optional schema definition
        
    Returns:
        True if all checks pass, False otherwise
    """
    checker = DataIntegrityChecker(dataset_name)
    passed, results = checker.validate_curated_promotion(df, schema)
    
    # Save validation report
    report_dir = Path(__file__).parent.parent.parent / "validation_reports"
    report_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_path = report_dir / f"{dataset_name}_validation_{timestamp}.json"
    
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
        
    logger.info(f"Validation report saved to: {report_path}")
    
    return passed

# Dataset-specific schemas
DATASET_SCHEMAS = {
    'tiktok_analytics': {
        'required_columns': ['date', 'artist', 'video_views', 'profile_views', 'likes', 'comments', 'shares'],
        'nullable_columns': ['new_followers'],
        'primary_keys': ['date', 'artist'],
        'column_types': {
            'date': 'date',
            'video_views': 'int',
            'likes': 'int',
            'comments': 'int',
            'shares': 'int'
        },
        'numeric_ranges': {
            'video_views': {'min': 0},
            'likes': {'min': 0},
            'comments': {'min': 0},
            'shares': {'min': 0}
        }
    },
    'spotify_audience': {
        'required_columns': ['date', 'artist', 'listeners', 'followers'],
        'primary_keys': ['date', 'artist'],
        'column_types': {
            'date': 'date',
            'listeners': 'int',
            'followers': 'int'
        },
        'numeric_ranges': {
            'listeners': {'min': 0},
            'followers': {'min': 0}
        }
    },
    'streaming_data': {
        'required_columns': ['date', 'platform', 'streams'],
        'nullable_columns': ['revenue', 'artist'],
        'column_types': {
            'date': 'date',
            'streams': 'int',
            'revenue': 'float'
        },
        'numeric_ranges': {
            'streams': {'min': 0},
            'revenue': {'min': 0}
        }
    },
    'financial_transactions': {
        'required_columns': ['date', 'description', 'amount'],
        'nullable_columns': ['category', 'platform'],
        'column_types': {
            'date': 'date',
            'amount': 'float'
        }
    }
}