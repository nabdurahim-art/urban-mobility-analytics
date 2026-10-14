import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app


env = os.getenv("FLASK_ENV", "development")
app = create_app(env)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5001")))
