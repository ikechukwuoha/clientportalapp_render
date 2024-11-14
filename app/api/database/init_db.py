import asyncio
import logging
from sqlalchemy.future import select
from app.api.models.role import Role
from app.api.models.permission import Permission
from app.api.models import Base
from app.api.database.db import async_engine, async_sessionmaker
from app.api.initial_data import roles, permissions, roles_permissions

# Configure logging to write to app.log
logging.basicConfig(
    filename='app.log',
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def init_db():
    try:
        # Create tables inside a transaction using the engine
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logging.info("Tables created successfully")

        # Open a new session for adding roles, permissions, and assigning them
        async with async_sessionmaker() as db:
            # Add roles
            for role_data in roles:
                result = await db.execute(select(Role).filter_by(name=role_data["name"]))
                role = result.scalars().first()
                if role:
                    logging.info(f"Role '{role_data['name']}' already exists.")
                else:
                    role = Role(**role_data)
                    db.add(role)
                    logging.info(f"Added role '{role_data['name']}' to the database.")
                    

            # Add permissions
            for permission_data in permissions:
                result = await db.execute(select(Permission).filter_by(name=permission_data["name"]))
                permission = result.scalars().first()
                if permission:
                    logging.info(f"Permission '{permission_data['name']}' already exists.")
                else:
                    permission = Permission(**permission_data)
                    db.add(permission)
                    logging.info(f"Added permission '{permission_data['name']}' to the database.")


        # Assign permissions to roles
            role_permission_tasks = []
            for role_name, permission_names in roles_permissions.items():
                # Fetch the role using async session
                role_query = db.execute(select(Role).filter_by(name=role_name))
                permission_queries = [db.execute(select(Permission).filter_by(name=permission_name)) for permission_name in permission_names]
                role_permission_tasks.append((role_query, permission_queries))

            role_permission_results = await asyncio.gather(*[asyncio.gather(role_query, *permission_queries) for role_query, permission_queries in role_permission_tasks])

            for (role_query_result, *permission_query_results), (role_name, permission_names) in zip(role_permission_results, roles_permissions.items()):
                role = role_query_result.scalars().first()
                
                if not role:
                    logging.warning(f"Role '{role_name}' not found!")
                    continue

                for permission_name, permission_query_result in zip(permission_names, permission_query_results):
                    permission = permission_query_result.scalars().first()
                    
                    if not permission:
                        logging.warning(f"Permission '{permission_name}' not found!")
                        continue
                    
                    # Ensure `role.permissions` is properly loaded
                    await db.refresh(role, attribute_names=['permissions'])

                    if permission not in role.permissions:
                        role.permissions.append(permission)
                        logging.info(f"Assigned permission '{permission_name}' to role '{role_name}'.")

            # Commit all changes
            await db.commit()
            logging.info("Role-permission assignments committed to the database.")
    except Exception as e:
        logging.error(f"Error initializing the database: {e}")
        # If there was an error, rollback the session
        async with async_sessionmaker() as db:
            await db.rollback()
    finally:
        # Ensure the session is closed
        async with async_sessionmaker() as db:
            await db.close()
