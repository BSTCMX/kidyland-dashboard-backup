"""
Cleanup service for permanently deleting soft-deleted records.

This service handles automatic hard deletion of records that have been
soft-deleted for more than the retention period (default: 30 days).
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models.service import Service
from models.product import Product
from models.user import User

logger = logging.getLogger(__name__)

# Retention period in days (configurable)
RETENTION_DAYS = 30


async def cleanup_deleted_services(
    retention_days: int = RETENTION_DAYS,
    db: Optional[AsyncSession] = None
) -> int:
    """
    Permanently delete services that have been soft-deleted for more than retention_days.
    
    Args:
        retention_days: Number of days to retain soft-deleted records (default: 30)
        db: Database session (if None, creates a new one)
    
    Returns:
        Number of services permanently deleted
    """
    if db is None:
        async for session in get_db():
            db = session
            break
    
    try:
        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        # Find services to permanently delete
        query = select(Service).where(
            Service.deleted_at.isnot(None),
            Service.deleted_at < cutoff_date
        )
        result = await db.execute(query)
        services_to_delete = result.scalars().all()
        
        if not services_to_delete:
            logger.debug("No services to permanently delete")
            return 0
        
        # Get IDs for logging
        service_ids = [str(s.id) for s in services_to_delete]
        service_names = [s.name for s in services_to_delete]
        
        # Permanently delete
        delete_query = delete(Service).where(
            Service.deleted_at.isnot(None),
            Service.deleted_at < cutoff_date
        )
        await db.execute(delete_query)
        await db.commit()
        
        logger.info(
            f"Permanently deleted {len(services_to_delete)} services "
            f"(soft-deleted before {cutoff_date.isoformat()}): "
            f"{', '.join(service_names[:5])}"
            + (f" and {len(services_to_delete) - 5} more" if len(services_to_delete) > 5 else "")
        )
        
        return len(services_to_delete)
        
    except Exception as e:
        logger.error(f"Error during cleanup of deleted services: {str(e)}", exc_info=True)
        if db:
            await db.rollback()
        raise
    finally:
        if db:
            await db.close()


async def cleanup_deleted_products(
    retention_days: int = RETENTION_DAYS,
    db: Optional[AsyncSession] = None
) -> int:
    """
    Permanently delete products that have been soft-deleted for more than retention_days.
    
    Args:
        retention_days: Number of days to retain soft-deleted records (default: 30)
        db: Database session (if None, creates a new one)
    
    Returns:
        Number of products permanently deleted
    """
    if db is None:
        async for session in get_db():
            db = session
            break
    
    try:
        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        # Find products to permanently delete
        query = select(Product).where(
            Product.deleted_at.isnot(None),
            Product.deleted_at < cutoff_date
        )
        result = await db.execute(query)
        products_to_delete = result.scalars().all()
        
        if not products_to_delete:
            logger.debug("No products to permanently delete")
            return 0
        
        # Get IDs for logging
        product_ids = [str(p.id) for p in products_to_delete]
        product_names = [p.name for p in products_to_delete]
        
        # Permanently delete
        delete_query = delete(Product).where(
            Product.deleted_at.isnot(None),
            Product.deleted_at < cutoff_date
        )
        await db.execute(delete_query)
        await db.commit()
        
        logger.info(
            f"Permanently deleted {len(products_to_delete)} products "
            f"(soft-deleted before {cutoff_date.isoformat()}): "
            f"{', '.join(product_names[:5])}"
            + (f" and {len(products_to_delete) - 5} more" if len(products_to_delete) > 5 else "")
        )
        
        return len(products_to_delete)
        
    except Exception as e:
        logger.error(f"Error during cleanup of deleted products: {str(e)}", exc_info=True)
        if db:
            await db.rollback()
        raise
    finally:
        if db:
            await db.close()


async def cleanup_deleted_users(
    retention_days: int = RETENTION_DAYS,
    db: Optional[AsyncSession] = None
) -> int:
    """
    Permanently delete users that have been soft-deleted for more than retention_days.
    
    Args:
        retention_days: Number of days to retain soft-deleted records (default: 30)
        db: Database session (if None, creates a new one)
    
    Returns:
        Number of users permanently deleted
    """
    if db is None:
        async for session in get_db():
            db = session
            break
    
    try:
        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        # Find users to permanently delete
        query = select(User).where(
            User.deleted_at.isnot(None),
            User.deleted_at < cutoff_date
        )
        result = await db.execute(query)
        users_to_delete = result.scalars().all()
        
        if not users_to_delete:
            logger.debug("No users to permanently delete")
            return 0
        
        # Get IDs for logging
        user_ids = [str(u.id) for u in users_to_delete]
        user_usernames = [u.username for u in users_to_delete]
        
        # Permanently delete
        delete_query = delete(User).where(
            User.deleted_at.isnot(None),
            User.deleted_at < cutoff_date
        )
        await db.execute(delete_query)
        await db.commit()
        
        logger.info(
            f"Permanently deleted {len(users_to_delete)} users "
            f"(soft-deleted before {cutoff_date.isoformat()}): "
            f"{', '.join(user_usernames[:5])}"
            + (f" and {len(users_to_delete) - 5} more" if len(users_to_delete) > 5 else "")
        )
        
        return len(users_to_delete)
        
    except Exception as e:
        logger.error(f"Error during cleanup of deleted users: {str(e)}", exc_info=True)
        if db:
            await db.rollback()
        raise
    finally:
        if db:
            await db.close()


async def periodic_cleanup_task(
    interval_hours: int = 24,
    retention_days: int = RETENTION_DAYS
):
    """
    Background task that periodically cleans up soft-deleted records.
    
    Runs cleanup every interval_hours and permanently deletes records
    that have been soft-deleted for more than retention_days.
    
    Args:
        interval_hours: Hours between cleanup runs (default: 24, i.e., daily)
        retention_days: Days to retain soft-deleted records (default: 30)
    """
    logger.info(
        f"Starting periodic cleanup task: interval={interval_hours}h, "
        f"retention={retention_days} days"
    )
    
    while True:
        try:
            await asyncio.sleep(interval_hours * 3600)  # Convert hours to seconds
            
            logger.debug("Running periodic cleanup of deleted records...")
            
            # Cleanup services
            services_deleted = await cleanup_deleted_services(retention_days=retention_days)
            
            # Cleanup products
            products_deleted = await cleanup_deleted_products(retention_days=retention_days)
            
            # Cleanup users
            users_deleted = await cleanup_deleted_users(retention_days=retention_days)
            
            total_deleted = services_deleted + products_deleted + users_deleted
            
            if total_deleted > 0:
                logger.info(
                    f"Cleanup completed: {services_deleted} services, {products_deleted} products, "
                    f"and {users_deleted} users permanently deleted"
                )
            else:
                logger.debug("Cleanup completed: no records to delete")
                
        except asyncio.CancelledError:
            logger.info("Periodic cleanup task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in periodic cleanup task: {str(e)}", exc_info=True)
            # Continue running even if one iteration fails
            await asyncio.sleep(60)  # Wait 1 minute before retrying

