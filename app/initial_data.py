roles = [
    {"name": "Admin"},
    {"name": "Editor"},
    {"name": "Viewer"},
    {"name": "Contributor"},
    {"name": "Moderator"},
    {"name": "Super Admin"},
    {"name": "Guest"},
    {"name": "Auditor"},
    {"name": "Content Manager"},
    {"name": "Support Agent"},
    {"name": "Developer"}
]

permissions = [
    {"name": "Create"},
    {"name": "Read"},
    {"name": "Update"},
    {"name": "Delete"},
    {"name": "Manage Users"},
    {"name": "Publish"},
    {"name": "Archive"},
    {"name": "Restore"},
    {"name": "Audit"},
    {"name": "Manage Settings"},
    {"name": "Support Users"},
    {"name": "Deploy"}
]

roles_permissions = {
    "Super Admin": ["Create", "Read", "Update", "Delete", "Manage Users", "Publish", "Archive", "Restore", "Audit", "Manage Settings", "Support Users", "Deploy"],
    "Admin": ["Create", "Read", "Update", "Delete", "Manage Users", "Publish", "Archive", "Manage Settings"],
    "Editor": ["Create", "Read", "Update", "Publish"],
    "user": ["Read"],
    "Contributor": ["Create", "Read", "Update"],
    "Moderator": ["Read", "Update", "Delete", "Audit"],
    "Guest": ["Read"],
    "Auditor": ["Read", "Audit"],
    "Content Manager": ["Create", "Read", "Update", "Publish", "Archive", "Restore"],
    "Support Agent": ["Read", "Support Users"],
    "Developer": ["Create", "Read", "Update", "Deploy"]
}
