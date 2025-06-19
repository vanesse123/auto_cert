import os
import click
from dotenv import load_dotenv

load_dotenv()

from app import create_app, db
from flask_migrate import Migrate


config_name = os.getenv("FLASK_CONFIG") or "default"
app = create_app(config_name)
migrate = Migrate(app, db)


@app.cli.command("test")
def test():
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


if __name__ == '__main__':
    app.run(host='127.0.0.1',port=5000,debug=True)
