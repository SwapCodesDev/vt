import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # Run host=0.0.0.0 so that other devices/TV screens on the network can access the 24/7 dashboard
    app.run(host='0.0.0.0', port=port, debug=True)
