from flask import render_template

from gifted import app, db


@app.errorhandler(401)
def unauthorized(error):
    db.session.rollback()
    return render_template('unauthorized.html', error=error), 401


@app.errorhandler(404)
def not_found(error):
    db.session.rollback()
    return render_template('not_found.html', error=error), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('internal_error.html', error=error), 500
