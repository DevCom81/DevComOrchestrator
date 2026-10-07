from devcom.bootstrap.app_factory import create_app
from devcom.bootstrap.settings import get_settings

settings = get_settings()
app = create_app(settings=settings)
