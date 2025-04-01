# Postcard Database

A web application for cataloging and managing a collection of postcards. Built with Python, Flask, and Supabase.

## Features

- Store and organize postcards with detailed metadata
- Upload front and back images of each postcard
- Filter and search postcards by various attributes
- Tag system for better organization
- Responsive design for desktop and mobile

## Requirements

- Python 3.8 or higher
- Flask web framework
- Supabase account (for database and storage)
- Modern web browser

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/postcard-database.git
   cd postcard-database
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a Supabase account and project:
   - Go to [Supabase](https://supabase.com/) and sign up
   - Create a new project
   - Go to SQL Editor and run the database schema from `database_schema.sql`
   - Create a storage bucket named 'postcard-images' with public access

5. Create a `.env` file:
   ```
   cp .env.example .env
   ```
   
   Edit the `.env` file and fill in your Supabase URL and API key.

6. Run the application:
   ```
   flask run
   ```
   
   The application will be available at http://127.0.0.1:5000/

## Project Structure

```
postcard_database/
│
├── app.py                  # Main Flask application
├── config.py               # Configuration settings
├── requirements.txt        # Python dependencies
│
├── static/                 # Static files
│   ├── css/
│   │   └── styles.css
│   ├── js/
│   │   └── main.js
│   └── img/
│
├── templates/              # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── postcards/
│   │   ├── add.html
│   │   ├── detail.html
│   │   ├── edit.html
│   │   └── list.html
│   └── error.html
│
└── utils/                  # Utility functions
    ├── __init__.py
    ├── db.py               # Supabase database connection
    ├── image_handler.py    # Image upload and processing
    └── template_filters.py # Custom Jinja filters
```

## Deploying to Production

For production deployment, consider the following:

1. Use a production WSGI server like Gunicorn:
   ```
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:8000 app:app
   ```

2. Set up environment variables for production:
   - Set `FLASK_ENV=production`
   - Generate a strong `SECRET_KEY`
   - Secure your Supabase API keys

3. Consider using a CDN for serving static files and images as your collection grows.

4. Set up regular database backups.

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.