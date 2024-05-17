FROM python:3.9

COPY requirements.txt .

# Install python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy code content
COPY . .

# Run migratiosn
RUN python manage.py migrate

# Start the server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]