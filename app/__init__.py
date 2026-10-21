from flask import Flask
from config import SECRET_KEY

def create_app():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY

    # Context processor to make variables available in all templates
    @app.context_processor
    def inject_globals():
        from config import DEFAULT_TERM, APP_NAME
        return {"current_term": DEFAULT_TERM, "app_name": APP_NAME}

    # Register blueprints
    from app.dashboard import bp as dashboard_bp
    app.register_blueprint(dashboard_bp)

    return app