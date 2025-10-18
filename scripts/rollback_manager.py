#!/usr/bin/env python3
"""
Rollback Manager - Backup and restore capability for all phases

Implements automatic backup and restore functionality for any phase.
Allows safe experimentation with ability to revert changes.

Features:
- Automatic backup before phase execution
- Directory-based snapshots
- File-level restore capability
- Backup retention policy
- Diff generation for review

Usage:
    from rollback_manager import RollbackManager
    
    rollback = RollbackManager()
    
    # Backup before risky operation
    backup_id = rollback.create_backup('phase_3', description="Before synthesis")
    
    try:
        risky_operation()
    except Exception as e:
        # Restore on failure
        rollback.restore_backup(backup_id)
"""

import json
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class BackupMetadata:
    """Metadata for a backup."""
    backup_id: str
    phase: str
    timestamp: str
    description: str
    paths_backed_up: List[str]
    total_size_bytes: int
    file_count: int
    backup_dir: str


class RollbackManager:
    """
    Backup and restore capability for any phase.
    
    Backup Strategy:
    - Automatic backup before each phase
    - Retention: Keep last 5 backups per phase
    - Storage: implementation_plans/backups/
    - Compressed: Optional (not implemented yet)
    
    Restore Strategy:
    - Full directory restore
    - Selective file restore
    - Diff preview before restore
    - Safe restore (backup current state first)
    """
    
    def __init__(self, backup_root: Optional[Path] = None):
        """Initialize rollback manager."""
        self.backup_root = backup_root or Path("implementation_plans/backups")
        self.backup_root.mkdir(parents=True, exist_ok=True)
        
        self.metadata_file = self.backup_root / "backup_metadata.json"
        self.metadata = self._load_metadata()
        
        logger.info("🔄 Rollback Manager initialized")
        logger.info(f"   Backup directory: {self.backup_root}")
        logger.info(f"   Total backups: {len(self.metadata['backups'])}")
    
    def _load_metadata(self) -> Dict:
        """Load backup metadata from disk."""
        if self.metadata_file.exists():
            return json.loads(self.metadata_file.read_text())
        else:
            return {
                'backups': [],
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
    
    def _save_metadata(self):
        """Save backup metadata to disk."""
        self.metadata['last_updated'] = datetime.now().isoformat()
        self.metadata_file.write_text(json.dumps(self.metadata, indent=2))
    
    def _generate_backup_id(self, phase: str) -> str:
        """Generate unique backup ID."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_hash = hashlib.md5(f"{phase}_{timestamp}".encode()).hexdigest()[:8]
        return f"{phase}_{timestamp}_{unique_hash}"
    
    def create_backup(
        self,
        phase: str,
        paths_to_backup: Optional[List[Path]] = None,
        description: str = ""
    ) -> str:
        """
        Create backup of specified paths.
        
        Args:
            phase: Phase identifier (e.g., 'phase_3')
            paths_to_backup: List of paths to backup (defaults to implementation_plans/)
            description: Human-readable description
        
        Returns:
            backup_id: Unique identifier for this backup
        """
        backup_id = self._generate_backup_id(phase)
        backup_dir = self.backup_root / backup_id
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Default to backing up implementation_plans/
        if paths_to_backup is None:
            paths_to_backup = [Path("implementation_plans")]
        
        logger.info(f"📦 Creating backup: {backup_id}")
        logger.info(f"   Phase: {phase}")
        logger.info(f"   Description: {description}")
        
        file_count = 0
        total_size = 0
        backed_up_paths = []
        
        for path in paths_to_backup:
            if not path.exists():
                logger.warning(f"   ⚠️  Path not found: {path}")
                continue
            
            if path.is_file():
                # Backup single file
                dest = backup_dir / path.name
                shutil.copy2(path, dest)
                file_count += 1
                total_size += path.stat().st_size
                backed_up_paths.append(str(path))
            
            elif path.is_dir():
                # Backup directory
                dest = backup_dir / path.name
                
                # Skip backups directory itself
                if path.resolve() == self.backup_root.resolve():
                    continue
                
                shutil.copytree(path, dest, symlinks=False, ignore=self._should_ignore)
                
                # Count files
                for file in dest.rglob('*'):
                    if file.is_file():
                        file_count += 1
                        total_size += file.stat().st_size
                
                backed_up_paths.append(str(path))
        
        # Create metadata
        metadata = BackupMetadata(
            backup_id=backup_id,
            phase=phase,
            timestamp=datetime.now().isoformat(),
            description=description,
            paths_backed_up=backed_up_paths,
            total_size_bytes=total_size,
            file_count=file_count,
            backup_dir=str(backup_dir)
        )
        
        # Save metadata
        self.metadata['backups'].append(asdict(metadata))
        self._save_metadata()
        
        # Cleanup old backups
        self._cleanup_old_backups(phase, keep_count=5)
        
        logger.info(f"   ✅ Backup created: {file_count} files, {total_size / 1024:.1f} KB")
        
        return backup_id
    
    def _should_ignore(self, dir_path: str, names: List[str]) -> List[str]:
        """Determine which files/dirs to ignore during backup."""
        ignore_patterns = {
            '__pycache__',
            '.pyc',
            '.git',
            '.DS_Store',
            'backups',  # Don't backup backups
            '.pytest_cache',
            'node_modules'
        }
        
        ignored = []
        for name in names:
            if any(pattern in name for pattern in ignore_patterns):
                ignored.append(name)
        
        return ignored
    
    def restore_backup(
        self,
        backup_id: str,
        safe_restore: bool = True,
        dry_run: bool = False
    ) -> bool:
        """
        Restore from backup.
        
        Args:
            backup_id: Backup to restore
            safe_restore: Create backup of current state before restoring
            dry_run: Preview what would be restored
        
        Returns:
            True if successful, False otherwise
        """
        # Find backup metadata
        backup_meta = None
        for backup in self.metadata['backups']:
            if backup['backup_id'] == backup_id:
                backup_meta = backup
                break
        
        if not backup_meta:
            logger.error(f"❌ Backup not found: {backup_id}")
            return False
        
        backup_dir = Path(backup_meta['backup_dir'])
        
        if not backup_dir.exists():
            logger.error(f"❌ Backup directory not found: {backup_dir}")
            return False
        
        logger.info(f"🔄 Restoring backup: {backup_id}")
        logger.info(f"   Phase: {backup_meta['phase']}")
        logger.info(f"   Created: {backup_meta['timestamp']}")
        logger.info(f"   Files: {backup_meta['file_count']}")
        
        if dry_run:
            logger.info("   🔍 DRY RUN MODE - No files will be restored")
            self._preview_restore(backup_dir)
            return True
        
        # Safe restore: backup current state first
        if safe_restore:
            logger.info("   📦 Creating safety backup of current state...")
            safety_backup_id = self.create_backup(
                phase=backup_meta['phase'],
                description=f"Safety backup before restoring {backup_id}"
            )
            logger.info(f"   ✅ Safety backup created: {safety_backup_id}")
        
        # Restore files
        try:
            for path_str in backup_meta['paths_backed_up']:
                source_path = backup_dir / Path(path_str).name
                dest_path = Path(path_str)
                
                if source_path.is_file():
                    # Restore single file
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_path, dest_path)
                    logger.info(f"   📄 Restored: {dest_path}")
                
                elif source_path.is_dir():
                    # Restore directory
                    if dest_path.exists():
                        shutil.rmtree(dest_path)
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copytree(source_path, dest_path, symlinks=False)
                    logger.info(f"   📁 Restored: {dest_path}")
            
            logger.info(f"✅ Restore complete: {backup_id}")
            return True
        
        except Exception as e:
            logger.error(f"❌ Restore failed: {e}")
            
            if safe_restore and 'safety_backup_id' in locals():
                logger.error(f"   Attempting to restore safety backup: {safety_backup_id}")
                return self.restore_backup(safety_backup_id, safe_restore=False)
            
            return False
    
    def _preview_restore(self, backup_dir: Path):
        """Preview what would be restored."""
        logger.info("\n   Files to be restored:")
        for file in backup_dir.rglob('*'):
            if file.is_file():
                relative = file.relative_to(backup_dir)
                logger.info(f"     - {relative}")
    
    def list_backups(self, phase: Optional[str] = None) -> List[Dict]:
        """
        List available backups.
        
        Args:
            phase: Filter by phase (None = all phases)
        
        Returns:
            List of backup metadata dictionaries
        """
        backups = self.metadata['backups']
        
        if phase:
            backups = [b for b in backups if b['phase'] == phase]
        
        # Sort by timestamp (newest first)
        backups = sorted(backups, key=lambda x: x['timestamp'], reverse=True)
        
        return backups
    
    def _cleanup_old_backups(self, phase: str, keep_count: int = 5):
        """
        Remove old backups, keeping only the most recent N per phase.
        
        Args:
            phase: Phase to clean up
            keep_count: Number of backups to keep
        """
        phase_backups = [b for b in self.metadata['backups'] if b['phase'] == phase]
        
        if len(phase_backups) <= keep_count:
            return
        
        # Sort by timestamp (oldest first)
        phase_backups = sorted(phase_backups, key=lambda x: x['timestamp'])
        
        # Remove oldest backups
        to_remove = phase_backups[:len(phase_backups) - keep_count]
        
        for backup in to_remove:
            backup_dir = Path(backup['backup_dir'])
            
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
                logger.info(f"   🗑️  Removed old backup: {backup['backup_id']}")
            
            # Remove from metadata
            self.metadata['backups'] = [
                b for b in self.metadata['backups']
                if b['backup_id'] != backup['backup_id']
            ]
        
        if to_remove:
            self._save_metadata()
    
    def delete_backup(self, backup_id: str) -> bool:
        """
        Manually delete a backup.
        
        Args:
            backup_id: Backup to delete
        
        Returns:
            True if successful, False otherwise
        """
        # Find backup
        backup_meta = None
        for backup in self.metadata['backups']:
            if backup['backup_id'] == backup_id:
                backup_meta = backup
                break
        
        if not backup_meta:
            logger.error(f"❌ Backup not found: {backup_id}")
            return False
        
        backup_dir = Path(backup_meta['backup_dir'])
        
        # Delete directory
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
            logger.info(f"🗑️  Deleted backup: {backup_id}")
        
        # Remove from metadata
        self.metadata['backups'] = [
            b for b in self.metadata['backups']
            if b['backup_id'] != backup_id
        ]
        self._save_metadata()
        
        return True
    
    def generate_backup_report(self) -> str:
        """Generate human-readable backup report."""
        report = f"""# Backup Report

**Generated:** {datetime.now().isoformat()}
**Total Backups:** {len(self.metadata['backups'])}
**Backup Directory:** {self.backup_root}

## Available Backups

| Backup ID | Phase | Created | Files | Size | Description |
|-----------|-------|---------|-------|------|-------------|
"""
        
        for backup in sorted(self.metadata['backups'], key=lambda x: x['timestamp'], reverse=True):
            size_kb = backup['total_size_bytes'] / 1024
            report += f"| {backup['backup_id']} | {backup['phase']} | {backup['timestamp']} | {backup['file_count']} | {size_kb:.1f} KB | {backup['description']} |\n"
        
        return report


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Initialize manager
    rollback = RollbackManager()
    
    # Create backup
    backup_id = rollback.create_backup(
        phase='test_phase',
        description="Test backup"
    )
    
    # List backups
    backups = rollback.list_backups()
    print(f"\n{len(backups)} backups available")
    
    # Preview restore
    if backups:
        rollback.restore_backup(backups[0]['backup_id'], dry_run=True)
    
    # Generate report
    print("\n" + rollback.generate_backup_report())

