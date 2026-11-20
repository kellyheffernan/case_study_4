FROM python:3.10-slim

WORKDIR /opt/app

# Copy dependencies first so Docker can cache their installation
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application files
COPY . .

# Gradio runs on port 7860
EXPOSE 7860

# Start the recipe chatbot
CMD ["python", "app.py"]
