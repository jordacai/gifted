from flask import render_template

from gifted import app, db


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('internal_error.html'), 500
