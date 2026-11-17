from app import create_app

# Create the app instance globally so Gunicorn can find it
app = create_app()

if __name__ == "__main__":
    # When running locally, use the development server
    app.run(debug=True, port=5000)