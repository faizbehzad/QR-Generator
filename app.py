from __future__ import annotations

from pathlib import Path

from flask import Flask, redirect, url_for as flask_url_for
from jinja2 import ChoiceLoader, FileSystemLoader

from QR_generator.routes import qr_generator_bp

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(PROJECT_DIR / "static"),
        static_url_path="/static",
    )
    app.jinja_loader = ChoiceLoader(
        [
            FileSystemLoader(str(BASE_DIR / "templates")),
            FileSystemLoader(str(PROJECT_DIR / "templates")),
        ]
    )
    app.register_blueprint(qr_generator_bp)

    main_site_routes = {
        "home": "/",
        "fbise_resources": "/fbise-resources",
        "ielts": "/ielts",
        "past_papers": "/past-papers",
        "university_resources": "/university-resources",
        "fbise_books": "/fbise-books",
        "pdf_converter": "/pdf-converter",
        "shop": "/shop",
        "article": "/news",
        "about": "/about",
        "view_cart": "/cart",
        "checkout": "/checkout",
    }

    def standalone_url_for(endpoint: str, **values) -> str:
        if endpoint in main_site_routes:
            return main_site_routes[endpoint]
        return flask_url_for(endpoint, **values)

    app.jinja_env.globals["url_for"] = standalone_url_for

    @app.route("/")
    def home():
        return redirect(flask_url_for("qr_generator.index"))

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5002)
