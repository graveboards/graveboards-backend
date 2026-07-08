from app.connexion_app import create_connexion_app
from app.logging import setup_logging

if __name__ == "__main__":
    setup_logging()
    connexion_app = create_connexion_app()
    connexion_app.run(f"{__file__}:create_connexion_app", factory=True)
