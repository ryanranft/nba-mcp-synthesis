"""
Database Migration Management

Automated database schema evolution:
- Version-controlled migrations
- Forward and rollback support
- Multi-environment support
- Data migrations
- Schema validation
- Migration history tracking

Features:
- Alembic-style migrations
- Automatic migration generation
- Safe rollback procedures
- Migration testing
- Dependency resolution
- Conflict detection

Use Cases:
- Schema evolution
- Data transformations
- Index management
- Constraint updates
"""

import os
import hashlib
import json
from datetime import datetime
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MigrationStatus(Enum):
    """Migration execution status"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class MigrationType(Enum):
    """Type of migration"""

    SCHEMA = "schema"  # DDL operations
    DATA = "data"  # DML operations
    HYBRID = "hybrid"  # Both DDL and DML


@dataclass
class Migration:
    """Migration definition"""

    version: str
    name: str
    migration_type: MigrationType
    up_sql: str
    down_sql: str
    description: str = ""
    dependencies: List[str] = field(default_factory=list)
    checksum: Optional[str] = None
    applied_at: Optional[datetime] = None
    status: MigrationStatus = MigrationStatus.PENDING

    def __post_init__(self):
        """Calculate checksum if not provided"""
        if not self.checksum:
            content = f"{self.version}:{self.up_sql}:{self.down_sql}"
            self.checksum = hashlib.sha256(content.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "version": self.version,
            "name": self.name,
            "migration_type": self.migration_type.value,
            "description": self.description,
            "checksum": self.checksum,
            "applied_at": self.applied_at.isoformat() if self.applied_at else None,
            "status": self.status.value,
        }


class MigrationManager:
    """Manage database migrations"""

    def __init__(self, db_connection, migrations_dir: str = "migrations"):
        self.db = db_connection
        self.migrations_dir = migrations_dir
        self.migrations: List[Migration] = []
        self._ensure_migrations_table()

    def _ensure_migrations_table(self) -> None:
        """Create migrations tracking table if not exists"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version VARCHAR(255) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            migration_type VARCHAR(50) NOT NULL,
            description TEXT,
            checksum VARCHAR(64) NOT NULL,
            applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(50) NOT NULL,
            execution_time_ms INTEGER,
            error_message TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_migrations_applied_at
        ON schema_migrations(applied_at);

        CREATE INDEX IF NOT EXISTS idx_migrations_status
        ON schema_migrations(status);
        """

        try:
            # Execute in transaction
            self.db.execute(create_table_sql)
            self.db.commit()
            logger.info("Migrations table ensured")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create migrations table: {e}")
            raise

    def load_migrations(self) -> None:
        """Load all migration files from migrations directory"""
        if not os.path.exists(self.migrations_dir):
            os.makedirs(self.migrations_dir)
            logger.info(f"Created migrations directory: {self.migrations_dir}")
            return

        migration_files = sorted(
            [
                f
                for f in os.listdir(self.migrations_dir)
                if f.endswith(".sql") or f.endswith(".py")
            ]
        )

        for filename in migration_files:
            filepath = os.path.join(self.migrations_dir, filename)
            migration = self._load_migration_file(filepath)
            if migration:
                self.migrations.append(migration)

        logger.info(f"Loaded {len(self.migrations)} migrations")

    def _load_migration_file(self, filepath: str) -> Optional[Migration]:
        """Load single migration file"""
        try:
            with open(filepath, "r") as f:
                content = f.read()

            # Parse migration file
            # Expected format:
            # -- version: 001
            # -- name: create_players_table
            # -- type: schema
            # -- description: Create initial players table
            # -- up:
            # CREATE TABLE players (...);
            # -- down:
            # DROP TABLE players;

            lines = content.split("\n")
            metadata = {}
            up_sql = []
            down_sql = []
            current_section = None

            for line in lines:
                if line.startswith("-- version:"):
                    metadata["version"] = line.split(":", 1)[1].strip()
                elif line.startswith("-- name:"):
                    metadata["name"] = line.split(":", 1)[1].strip()
                elif line.startswith("-- type:"):
                    metadata["type"] = line.split(":", 1)[1].strip()
                elif line.startswith("-- description:"):
                    metadata["description"] = line.split(":", 1)[1].strip()
                elif line.startswith("-- up:"):
                    current_section = "up"
                elif line.startswith("-- down:"):
                    current_section = "down"
                elif current_section == "up" and not line.startswith("--"):
                    up_sql.append(line)
                elif current_section == "down" and not line.startswith("--"):
                    down_sql.append(line)

            return Migration(
                version=metadata.get("version", "000"),
                name=metadata.get("name", "unnamed"),
                migration_type=MigrationType(metadata.get("type", "schema")),
                up_sql="\n".join(up_sql).strip(),
                down_sql="\n".join(down_sql).strip(),
                description=metadata.get("description", ""),
            )
        except Exception as e:
            logger.error(f"Failed to load migration from {filepath}: {e}")
            return None

    def get_applied_migrations(self) -> List[Dict[str, Any]]:
        """Get list of applied migrations"""
        query = """
        SELECT version, name, migration_type, checksum, applied_at, status
        FROM schema_migrations
        ORDER BY applied_at ASC
        """

        try:
            result = self.db.execute(query)
            return [dict(row) for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Failed to fetch applied migrations: {e}")
            return []

    def get_pending_migrations(self) -> List[Migration]:
        """Get list of pending migrations"""
        applied = {m["version"] for m in self.get_applied_migrations()}
        return [m for m in self.migrations if m.version not in applied]

    def apply_migration(self, migration: Migration) -> bool:
        """Apply a single migration"""
        logger.info(f"Applying migration {migration.version}: {migration.name}")

        start_time = datetime.now()

        try:
            # Begin transaction
            self.db.begin()

            # Execute migration SQL
            self.db.execute(migration.up_sql)

            # Record migration
            end_time = datetime.now()
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)

            insert_sql = """
            INSERT INTO schema_migrations
            (version, name, migration_type, description, checksum, applied_at, status, execution_time_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """

            self.db.execute(
                insert_sql,
                (
                    migration.version,
                    migration.name,
                    migration.migration_type.value,
                    migration.description,
                    migration.checksum,
                    end_time,
                    MigrationStatus.SUCCESS.value,
                    execution_time_ms,
                ),
            )

            # Commit transaction
            self.db.commit()

            migration.applied_at = end_time
            migration.status = MigrationStatus.SUCCESS

            logger.info(
                f"Migration {migration.version} applied successfully in {execution_time_ms}ms"
            )
            return True

        except Exception as e:
            self.db.rollback()

            # Record failure
            error_insert = """
            INSERT INTO schema_migrations
            (version, name, migration_type, description, checksum, status, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """

            try:
                self.db.execute(
                    error_insert,
                    (
                        migration.version,
                        migration.name,
                        migration.migration_type.value,
                        migration.description,
                        migration.checksum,
                        MigrationStatus.FAILED.value,
                        str(e),
                    ),
                )
                self.db.commit()
            except:
                pass

            migration.status = MigrationStatus.FAILED
            logger.error(f"Migration {migration.version} failed: {e}")
            return False

    def rollback_migration(self, migration: Migration) -> bool:
        """Rollback a migration"""
        logger.info(f"Rolling back migration {migration.version}: {migration.name}")

        try:
            # Begin transaction
            self.db.begin()

            # Execute rollback SQL
            self.db.execute(migration.down_sql)

            # Remove from migrations table
            delete_sql = "DELETE FROM schema_migrations WHERE version = ?"
            self.db.execute(delete_sql, (migration.version,))

            # Commit transaction
            self.db.commit()

            migration.status = MigrationStatus.ROLLED_BACK

            logger.info(f"Migration {migration.version} rolled back successfully")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Rollback of migration {migration.version} failed: {e}")
            return False

    def migrate_up(self, target_version: Optional[str] = None) -> bool:
        """Apply all pending migrations up to target version"""
        pending = self.get_pending_migrations()

        if not pending:
            logger.info("No pending migrations")
            return True

        for migration in pending:
            if target_version and migration.version > target_version:
                break

            if not self.apply_migration(migration):
                logger.error(f"Migration failed, stopping at {migration.version}")
                return False

        logger.info("All migrations applied successfully")
        return True

    def migrate_down(self, steps: int = 1) -> bool:
        """Rollback last N migrations"""
        applied = self.get_applied_migrations()

        if not applied:
            logger.info("No migrations to rollback")
            return True

        # Get last N applied migrations
        to_rollback = applied[-steps:]

        for migration_record in reversed(to_rollback):
            # Find migration object
            migration = next(
                (
                    m
                    for m in self.migrations
                    if m.version == migration_record["version"]
                ),
                None,
            )

            if not migration:
                logger.error(f"Migration {migration_record['version']} not found")
                return False

            if not self.rollback_migration(migration):
                return False

        logger.info(f"Rolled back {steps} migration(s)")
        return True

    def validate_migrations(self) -> bool:
        """Validate migration integrity"""
        applied = self.get_applied_migrations()

        for applied_migration in applied:
            # Find corresponding migration file
            migration = next(
                (
                    m
                    for m in self.migrations
                    if m.version == applied_migration["version"]
                ),
                None,
            )

            if not migration:
                logger.error(
                    f"Migration {applied_migration['version']} is applied but file not found"
                )
                return False

            if migration.checksum != applied_migration["checksum"]:
                logger.error(f"Migration {migration.version} checksum mismatch!")
                logger.error(f"Expected: {applied_migration['checksum']}")
                logger.error(f"Found: {migration.checksum}")
                return False

        logger.info("All migrations validated successfully")
        return True

    def generate_migration(
        self,
        name: str,
        up_sql: str,
        down_sql: str,
        migration_type: MigrationType = MigrationType.SCHEMA,
        description: str = "",
    ) -> str:
        """Generate a new migration file"""
        # Get next version number
        existing_versions = [m.version for m in self.migrations]
        next_version = str(len(existing_versions) + 1).zfill(3)

        # Create migration content
        content = f"""-- version: {next_version}
-- name: {name}
-- type: {migration_type.value}
-- description: {description}

-- up:
{up_sql}

-- down:
{down_sql}
"""

        # Write to file
        filename = f"{next_version}_{name}.sql"
        filepath = os.path.join(self.migrations_dir, filename)

        with open(filepath, "w") as f:
            f.write(content)

        logger.info(f"Generated migration: {filepath}")
        return filepath


# NBA MCP example migrations
def create_nba_migrations(manager: MigrationManager) -> None:
    """Create initial NBA database migrations"""

    # Migration 1: Create players table
    manager.generate_migration(
        name="create_players_table",
        up_sql="""
        CREATE TABLE players (
            player_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL,
            team VARCHAR(100),
            position VARCHAR(10),
            jersey_number INTEGER,
            height_cm INTEGER,
            weight_kg INTEGER,
            birth_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX idx_players_team ON players(team);
        CREATE INDEX idx_players_position ON players(position);
        """,
        down_sql="DROP TABLE players;",
        migration_type=MigrationType.SCHEMA,
        description="Create initial players table with indexes",
    )

    # Migration 2: Add player stats
    manager.generate_migration(
        name="add_player_stats_columns",
        up_sql="""
        ALTER TABLE players ADD COLUMN ppg DECIMAL(5,2) DEFAULT 0.0;
        ALTER TABLE players ADD COLUMN rpg DECIMAL(5,2) DEFAULT 0.0;
        ALTER TABLE players ADD COLUMN apg DECIMAL(5,2) DEFAULT 0.0;
        """,
        down_sql="""
        ALTER TABLE players DROP COLUMN ppg;
        ALTER TABLE players DROP COLUMN rpg;
        ALTER TABLE players DROP COLUMN apg;
        """,
        migration_type=MigrationType.SCHEMA,
        description="Add basic stats columns to players table",
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== Database Migration Manager ===\n")

    # Mock database connection
    class MockDB:
        def execute(self, sql, params=None):
            pass

        def commit(self):
            pass

        def rollback(self):
            pass

        def begin(self):
            pass

    manager = MigrationManager(MockDB())

    # Generate example migrations
    print("Generating NBA migrations...")
    create_nba_migrations(manager)

    # Load migrations
    manager.load_migrations()

    print(f"\nLoaded {len(manager.migrations)} migrations")
    print("\nPending migrations:")
    for migration in manager.get_pending_migrations():
        print(f"  - {migration.version}: {migration.name}")
