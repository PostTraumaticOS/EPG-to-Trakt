# EPG-to-Trakt
A tool to convert JSON formatted EPG to Trakt List

## Code Documentation

This document provides an overview of the code along with necessary setup instructions, configuration details, and requirements for running the provided Python script.

### Overview

The provided Python script facilitates interactions with the Trakt API for managing lists of TV shows and episodes. It allows users to create a Trakt list, search for shows and episodes, and add them to the list.

### Setup Instructions

1. **Install Required Packages**: Ensure that the required Python packages are installed. You can install them using the `requirements.txt` file provided.

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure `config.json`**: Fill out the `config.json` file with your Trakt API credentials and other necessary details. Ensure that the `json_file_name` points to the correct JSON file containing the TV show and episode data.

3. **Run the Script**: Execute the Python script `trakt_api.py`:

   ```bash
   python trakt_api.py
   ```

4. **Follow Authorization Steps**: Follow the prompts to authorize the application and obtain an authorization code.

5. **View Results**: Once the script completes execution, check the Trakt website to view the created list and added episodes.

### Configuration Details

- **`config.json`**: This file contains the configuration parameters required for the script to interact with the Trakt API.

  - `user_id`: Your Trakt user ID.
  - `client_id`: Your Trakt API client ID.
  - `client_secret`: Your Trakt API client secret.
  - `redirect_uri`: Redirect URI for OAuth authentication.
  - `json_file_name`: Name of the JSON file containing TV show and episode data.
  - `list_data`: Details for creating the Trakt list.

### Requirements

The script relies on the following Python packages:

- `requests`: For making HTTP requests to the Trakt API.
- `fuzzywuzzy`: For fuzzy matching of show and episode titles.
- `json`: For reading JSON files.

Ensure that these packages are installed using the provided `requirements.txt` file.

#### `requirements.txt`

```plaintext
requests==2.26.0
fuzzywuzzy==0.18.0
```
