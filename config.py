import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "hard to guess string")

    @staticmethod
    def create_db_uri():
        db_user = os.getenv("DB_USER", "new_user")
        db_password = os.getenv("DB_PASSWORD", "12345678")
        db_host = os.getenv("DB_HOST", "127.0.0.1")
        db_port = os.getenv("DB_PORT", "3306")
        db_name = os.getenv("DB_NAME", "cert")
        print(f"DB_USER={db_user}, DB_PASSWORD={db_password}, DB_HOST={db_host}, DB_PORT={db_port}, DB_NAME={db_name}")
        return f"mariadb+mariadbconnector://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = Config.create_db_uri()


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("TEST_DATABASE_URI") or Config.create_db_uri()
    )


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URI") or Config.create_db_uri()


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
