import os
from app.config.settings import Settings

def test_settings_default():
    settings = Settings(_env_file=None)
    assert settings.env == "development"
    assert settings.port == 8000

def test_settings_override():
    os.environ["ENV"] = "production"
    settings = Settings(_env_file=None)
    assert settings.env == "production"
    del os.environ["ENV"]
