import logging
from sqlalchemy.orm import Session
from app.models.role import Role
from app.models.permission import Permission
from app.models import Base
from app.database.db import engine, SessionLocal
from app.initial_data import roles, permissions, role_permissions

# Configure logging to write to app.log
logging.basicConfig(
    filename='app.log',      # Log messages will be written to app.log
    filemode='a',           # Append mode (use 'w' for overwrite)
    level=logging.INFO,     # Set the logging level
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log message format
)

def init_db():
    db = SessionLocal()
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logging.info("Tables created successfully")

        # Add roles
        for role_data in roles:
            role = db.query(Role).filter_by(name=role_data["name"]).first()
            if role:
                logging.info(f"Role '{role_data['name']}' already exists.")
            else:
                role = Role(**role_data)
                db.add(role)
                logging.info(f"Added role '{role_data['name']}' to the database.")
        
        # Add permissions
        for permission_data in permissions:
            permission = db.query(Permission).filter_by(name=permission_data["name"]).first()
            if permission:
                logging.info(f"Permission '{permission_data['name']}' already exists.")
            else:
                permission = Permission(**permission_data)
                db.add(permission)
                logging.info(f"Added permission '{permission_data['name']}' to the database.")
        
        # Commit the changes to the database
        db.commit()
        logging.info("Roles and permissions added to the database successfully.")

        # Assign permissions to roles
        for role_name, permission_names in role_permissions.items():
            role = db.query(Role).filter_by(name=role_name).first()
            if not role:
                logging.warning(f"Role '{role_name}' not found!")
                continue

            for permission_name in permission_names:
                permission = db.query(Permission).filter_by(name=permission_name).first()
                if not permission:
                    logging.warning(f"Permission '{permission_name}' not found!")
                    continue
                
                if permission not in role.permissions:
                    role.permissions.append(permission)
                    logging.info(f"Assigned permission '{permission_name}' to role '{role_name}'.")
        
        # Commit role-permission assignments
        db.commit()
        logging.info("Role-permission assignments committed to the database.")

    except Exception as e:
        logging.error(f"Error initializing the database: {e}")
        db.rollback()  # Roll back if something goes wrong
    finally:
        db.close()
