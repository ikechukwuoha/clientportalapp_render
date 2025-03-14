# FRAPPE_BASE_URL = "http://clientportal.org:8080"
FRAPPE_BASE_URL="https://lassod.erp.staging.purpledove.net"
FRAPPE_API_KEY = "your_api_key"
FRAPPE_API_SECRET = "your_api_secret"

HEADERS = {
    "Authorization": f"token {FRAPPE_API_KEY}:{FRAPPE_API_SECRET}"
}
