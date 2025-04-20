from flask import Flask
import os
from flask_cors import CORS

import init_db
from api.data_routes import data_bp

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev', # Default secret key for development
        DATABASE=os.path.join(app.instance_path, 'database.db'),
    )

    CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    # Ensure instance folder exists for schema generation
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize database functions with app
    init_db.init_app(app) # Initialize db commands

    # Register blueprints
    app.register_blueprint(data_bp, url_prefix='/api')

    # A simple health check route to see if app is up and running :)
    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
