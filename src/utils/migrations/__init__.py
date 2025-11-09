"""
Database Migrations System

Automatische Datenbank-Schema-Updates beim Start.
Jede Migration wird nur einmal ausgeführt.
"""

from .migration_manager import MigrationManager

__all__ = ['MigrationManager']
