from flask import Flask
from config import config
from .models import db
from flask_wtf.csrf import CSRFProtect
from flask_bootstrap import Bootstrap5
from .extensions import login_manager

bootstrap = Bootstrap5()
csrf = CSRFProtect()

def create_app(config_name):
    app = Flask(__name__)

  
    csrf.init_app(app)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    bootstrap.init_app(app)
    login_manager.init_app(app)
    db.init_app(app)
    

    from app.main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    from app.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)
    from app.user import user as user_blueprint
    app.register_blueprint(user_blueprint)
    from app.certificate import certificate as certificate_blueprint
    app.register_blueprint(certificate_blueprint)
    from app.courses import courses as courses_blueprint
    app.register_blueprint(courses_blueprint, url_prefix='/courses')
    from app.applications import applications as applications_blueprint
    app.register_blueprint(applications_blueprint)

    
    return app
