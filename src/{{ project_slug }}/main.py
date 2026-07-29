from .application import Application
from .settings import Config

app = Application(Config.load()).create_app()
