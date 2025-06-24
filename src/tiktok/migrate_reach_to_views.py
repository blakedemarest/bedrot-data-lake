"""
TikTok Reach→Views Migration Script

This script migrates historical TikTok data by:
1. Replacing "reach" fields with "Video Views" in curated data
2. Adding empty "Followers" column for consistency with new schema
3. Backing up original files before migration
4. Updating column names across all TikTok data files

Usage:
    python migrate_reach_to_views.py --dry-run  # Preview changes
    python migrate_reach_to_views.py --execute  # Apply changes
"""

import argparse
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict

import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
PROJECT_ROOT = Path(os.environ.get('PROJECT_ROOT', '.'))

# Directories to check for TikTok data
DIRECTORIES_TO_MIGRATE = [
    PROJECT_ROOT / "curated" / "tiktok",
    PROJECT_ROOT / "staging",
    PROJECT_ROOT / "archive" / "tiktok",
    PROJECT_ROOT,  # Root directory CSV files
]

# Column mappings for migration
COLUMN_MAPPINGS = {
    'reach': 'Video Views',
    'page_views': 'Profile Views',
    'video_views': 'Video Views',
    'profile_views': 'Profile Views',
    'followers': 'Followers',
    'likes': 'Likes',
    'comments': 'Comments',
    'shares': 'Shares'
}

# Expected final column order for curated data (existing + 2 new columns)
CURATED_COLUMN_ORDER = [
    'artist', 'zone', 'date', 'Video Views', 'Profile Views', 
    'Likes', 'Comments', 'Shares', 'Year', 'engagement_rate',
    'Followers', 'new_followers'  # NEW: Only these two columns should be added
]

class TikTokMigration:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.backup_dir = PROJECT_ROOT / "archive" / "migration_backup" / datetime.now().strftime('%Y%m%d_%H%M%S')
        self.migration_log = []
        
        if not self.dry_run:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def log(self, message: str):
        """Add message to migration log."""
        print(message)
        self.migration_log.append(message)
    
    def backup_file(self, file_path: Path) -> Path:
        """Create backup of file before migration."""
        if self.dry_run:
            return file_path
        
        backup_path = self.backup_dir / file_path.name
        shutil.copy2(file_path, backup_path)
        self.log(f"[BACKUP] {file_path.name} → {backup_path}")
        return backup_path
    
    def find_tiktok_files(self) -> List[Path]:
        """Find all TikTok-related CSV files that need migration."""
        tiktok_files = []
        
        for directory in DIRECTORIES_TO_MIGRATE:
            if directory.exists():
                # Look for TikTok CSV files
                patterns = [
                    "tiktok*.csv",
                    "*tiktok*.csv", 
                    "tiktok_analytics*.csv",
                    "tiktok_daily_metrics*.csv"
                ]
                
                for pattern in patterns:
                    tiktok_files.extend(directory.glob(pattern))
        
        # Remove duplicates
        unique_files = list(set(tiktok_files))
        unique_files.sort()
        
        self.log(f"[DISCOVERY] Found {len(unique_files)} TikTok CSV files")
        for file_path in unique_files:
            self.log(f"  - {file_path.relative_to(PROJECT_ROOT)}")
        
        return unique_files
    
    def analyze_file(self, file_path: Path) -> Dict:
        """Analyze a CSV file to determine migration needs."""
        try:
            df = pd.read_csv(file_path)
            
            analysis = {
                'path': file_path,
                'rows': len(df),
                'columns': list(df.columns),
                'has_reach': 'reach' in df.columns,
                'has_followers': 'followers' in df.columns or 'Followers' in df.columns,
                'needs_migration': False,
                'migration_actions': []
            }
            
            # Check if migration is needed
            if 'reach' in df.columns:
                analysis['needs_migration'] = True
                analysis['migration_actions'].append('rename reach → Video Views')
            
            if 'Followers' not in df.columns:
                analysis['needs_migration'] = True
                analysis['migration_actions'].append('add Followers column')
            
            if 'new_followers' not in df.columns:
                analysis['needs_migration'] = True
                analysis['migration_actions'].append('add new_followers column')
            
            # Check for other column standardization needs
            for old_col, new_col in COLUMN_MAPPINGS.items():
                if old_col in df.columns and old_col != new_col.lower():
                    analysis['needs_migration'] = True
                    analysis['migration_actions'].append(f'rename {old_col} → {new_col}')
            
            return analysis
            
        except Exception as e:
            self.log(f"[ERROR] Failed to analyze {file_path}: {e}")
            return {'path': file_path, 'error': str(e)}
    
    def migrate_file(self, file_path: Path, analysis: Dict) -> bool:
        """Migrate a single CSV file."""
        if not analysis.get('needs_migration', False):
            self.log(f"[SKIP] {file_path.name} - no migration needed")
            return True
        
        try:
            # Backup original file
            self.backup_file(file_path)
            
            # Load and migrate data
            df = pd.read_csv(file_path)
            original_columns = list(df.columns)
            
            self.log(f"[MIGRATE] {file_path.name} ({len(df)} rows)")
            
            # Apply column mappings
            column_renames = {}
            for old_col in df.columns:
                # Check direct mappings
                if old_col in COLUMN_MAPPINGS:
                    new_col = COLUMN_MAPPINGS[old_col]
                    if old_col != new_col:
                        column_renames[old_col] = new_col
                        self.log(f"  - Rename: {old_col} → {new_col}")
                
                # Special case: 'reach' → 'Video Views'
                elif old_col.lower() == 'reach':
                    column_renames[old_col] = 'Video Views'
                    self.log(f"  - Rename: {old_col} → Video Views")
            
            # Apply renames
            if column_renames:
                df = df.rename(columns=column_renames)
            
            # Add missing Followers column if needed  
            if 'Followers' not in df.columns:
                df['Followers'] = 0
                self.log(f"  - Added: Followers column (default 0)")
            
            # Add missing new_followers column if needed
            if 'new_followers' not in df.columns:
                df['new_followers'] = 0
                self.log(f"  - Added: new_followers column (default 0)")
            
            # Standardize column names (capitalize first letter)
            standardized_columns = {}
            for col in df.columns:
                if col.lower() in ['video views', 'profile views', 'likes', 'comments', 'shares', 'followers']:
                    # Ensure proper capitalization
                    if col.lower() == 'video views':
                        standardized_columns[col] = 'Video Views'
                    elif col.lower() == 'profile views':
                        standardized_columns[col] = 'Profile Views'
                    elif col.lower() == 'followers':
                        standardized_columns[col] = 'Followers'
                    elif col.lower() == 'likes':
                        standardized_columns[col] = 'Likes'
                    elif col.lower() == 'comments':
                        standardized_columns[col] = 'Comments'
                    elif col.lower() == 'shares':
                        standardized_columns[col] = 'Shares'
            
            if standardized_columns:
                df = df.rename(columns=standardized_columns)
                for old_col, new_col in standardized_columns.items():
                    self.log(f"  - Standardize: {old_col} → {new_col}")
            
            # Reorder columns for curated files
            if 'curated' in str(file_path):
                available_columns = [col for col in CURATED_COLUMN_ORDER if col in df.columns]
                other_columns = [col for col in df.columns if col not in CURATED_COLUMN_ORDER]
                final_columns = available_columns + other_columns
                df = df[final_columns]
                self.log(f"  - Reordered columns for curated format")
            
            # Save migrated file
            if not self.dry_run:
                df.to_csv(file_path, index=False)
                self.log(f"  - Saved migrated file")
            else:
                self.log(f"  - [DRY RUN] Would save migrated file")
            
            self.log(f"[SUCCESS] Migrated {file_path.name}")
            return True
            
        except Exception as e:
            self.log(f"[ERROR] Failed to migrate {file_path}: {e}")
            return False
    
    def run_migration(self) -> bool:
        """Run the complete migration process."""
        self.log(f"[START] TikTok Reach→Views Migration (dry_run={self.dry_run})")
        
        # Find all TikTok files
        tiktok_files = self.find_tiktok_files()
        
        if not tiktok_files:
            self.log("[INFO] No TikTok files found for migration")
            return True
        
        # Analyze each file
        migration_plan = []
        for file_path in tiktok_files:
            analysis = self.analyze_file(file_path)
            migration_plan.append(analysis)
        
        # Show migration plan
        files_needing_migration = [a for a in migration_plan if a.get('needs_migration', False)]
        
        self.log(f"\n[PLAN] Migration Summary:")
        self.log(f"  - Total files analyzed: {len(migration_plan)}")
        self.log(f"  - Files needing migration: {len(files_needing_migration)}")
        self.log(f"  - Files already up-to-date: {len(migration_plan) - len(files_needing_migration)}")
        
        if files_needing_migration:
            self.log(f"\n[ACTIONS] Files to be migrated:")
            for analysis in files_needing_migration:
                self.log(f"  - {analysis['path'].name}:")
                for action in analysis['migration_actions']:
                    self.log(f"    • {action}")
        
        if self.dry_run:
            self.log(f"\n[DRY RUN] Use --execute to apply these changes")
            return True
        
        # Execute migration
        self.log(f"\n[EXECUTE] Applying migrations...")
        
        success_count = 0
        for analysis in files_needing_migration:
            if self.migrate_file(analysis['path'], analysis):
                success_count += 1
        
        self.log(f"\n[COMPLETE] Migration finished:")
        self.log(f"  - Successfully migrated: {success_count}/{len(files_needing_migration)} files")
        self.log(f"  - Backup directory: {self.backup_dir}")
        
        # Save migration log
        log_file = self.backup_dir / "migration_log.txt"
        with open(log_file, 'w') as f:
            f.write('\n'.join(self.migration_log))
        self.log(f"  - Migration log: {log_file}")
        
        return success_count == len(files_needing_migration)

def main():
    parser = argparse.ArgumentParser(description="Migrate TikTok data from reach→views schema")
    parser.add_argument("--dry-run", action="store_true", default=True,
                       help="Preview changes without modifying files (default)")
    parser.add_argument("--execute", action="store_true",
                       help="Apply migrations to files")
    
    args = parser.parse_args()
    
    # Execute mode overrides dry-run
    dry_run = not args.execute
    
    migration = TikTokMigration(dry_run=dry_run)
    success = migration.run_migration()
    
    if not success:
        print("\n[ERROR] Migration completed with errors")
        exit(1)
    else:
        print("\n[SUCCESS] Migration completed successfully")

if __name__ == "__main__":
    main()