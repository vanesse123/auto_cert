from flask import render_template
from . import main

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/verify')
def verify():
    return render_template('verify.html')
