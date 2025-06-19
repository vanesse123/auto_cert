from flask import render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from . import user

@user.route('/profile')
@login_required
def profile():
    return render_template('user/profile2.html')