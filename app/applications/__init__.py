from flask import Blueprint

applications = Blueprint('applications', __name__)

from . import views