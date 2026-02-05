# Installation & Setup

## Prerequisites

- **Python 3.8+**
- **pip** (Python package manager)
- **git** (to clone the repository)

## Step 1: Download the Source Code

Clone the repository and navigate into the directory:

```bash
git clone https://github.com/searxng/data-searxng.git
cd data-searxng
```

_(Note: Replace the URL with your actual repository URL if different)_

## Step 2: Install Dependencies

Create a virtual environment (optional but recommended) and install required packages:

```bash
# Create virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Activate it (Linux/Mac)
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

## Step 3: Configuration

The main configuration file is located at `talven/settings.yml`.
You can edit this file to enable/disable engines, change server settings, and more.

See [Configuration Guide](configuration.md) for details.

## Step 4: Run the API

Start the server:

```bash
python talven/webapp.py
```

The API will be available at `http://127.0.0.1:8888`.

## Step 5: Verify

Visit `http://127.0.0.1:8888/` in your browser or use curl:

```bash
curl http://127.0.0.1:8888/
```

You should see a JSON response confirming the service is running.
