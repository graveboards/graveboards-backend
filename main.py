from app.connexion_app import create_connexion_app

if __name__ == "__main__":
    connexion_app = create_connexion_app()
    connexion_app.run(f"{__file__}:create_connexion_app", factory=True)
