"""
Seeds package for CRM database initialization.

This package provides comprehensive seeding functionality for the CRM system,
including realistic sample data for all models with proper relationships.

Usage:
    python -m app.seeds.seed
    
Or programmatically:
    from app.seeds.seed import DatabaseSeeder
    
    with DatabaseSeeder() as seeder:
        seeder.run_full_seed()
"""

from .factories import DataFactory
from .seed import DatabaseSeeder

__all__ = ["DataFactory", "DatabaseSeeder"]
