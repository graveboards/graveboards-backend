from pathlib import Path

from app.connexion_app import create_connexion_app

if __name__ == "__main__":
    connexion_app = create_connexion_app()
    connexion_app.run(f"{Path(__file__).stem}:create_connexion_app", factory=True, log_config="logging.uvicorn.yaml")
