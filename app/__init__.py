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
    from app.students import bp as students_bp
    from app.payments import bp as payments_bp
    from app.scores import bp as scores_bp
    from app.reports import bp as reports_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(scores_bp)
    app.register_blueprint(reports_bp)

    return app