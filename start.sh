#!/bin/bash
# Initialize database with sample data
python init_data.py

# Start the application
gunicorn socialbook:app
