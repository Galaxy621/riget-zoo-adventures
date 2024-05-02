import os

from . import account, hotel, pages

from flask import Flask

def create_app():
    key = os.urandom(12)
    app = Flask(__name__)
    
    if app.debug:
        app.secret_key = "DEBUGGING_KEY"
    else:
        app.secret_key = key

    app.register_blueprint(account.bp)
    app.register_blueprint(hotel.bp)
    app.register_blueprint(pages.bp)

    return app