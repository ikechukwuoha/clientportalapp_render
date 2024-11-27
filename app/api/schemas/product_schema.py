from pydantic import BaseModel

class ItemUpdateRequest(BaseModel):
    name: str
    item_name: str = None
    item_group: str = None
    description: str = None
    custom_security: str = None
    benefits: list[dict] = []  # Example: [{"title": "Benefit1", "description": "Desc1"}]
    images: list[str] = []  # List of image URLs
    price: float = None  # New price if any