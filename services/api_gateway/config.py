import os

class Config:
    # Read values with fallbacks if not defined in .env
    GATEWAY_PORT = int(os.getenv("GATEWAY_PORT", 8008))

    # Grouped namespaces for microservices
    # SERVICES = {
    # }

config = Config()