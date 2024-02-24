import json
import requests
from fuzzywuzzy import process


def read_config():
    """
    Read the configuration from the config.json file.

    Returns:
        dict: Configuration data.
    """
    try:
        with open('config.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print("Error: Config file not found.")
        return None
    except json.JSONDecodeError:
        print("Error: Config file is not a valid JSON.")
        return None


config = read_config()
USER_ID = config['user_id']
CLIENT_ID = config['client_id']
CLIENT_SECRET = config['client_secret']
REDIRECT_URI = config['redirect_uri']
JSON_FILE_NAME = config['json_file_name']
LIST_DATA = config['list_data']


def read_json_file(filename):
    """
    Read JSON data from a file.

    Args:
        filename (str): Name of the JSON file.

    Returns:
        dict: JSON data.
    """
    try:
        with open(filename, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: JSON file '{filename}' not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: JSON file '{filename}' is not a valid JSON.")
        return None


def get_access_token(authorization_code):
    """
    Get access token using the authorization code.

    Args:
        authorization_code (str): Authorization code.

    Returns:
        str: Access token.
    """
    token_url = 'https://trakt.tv/oauth/token'
    token_data = {
        'code': authorization_code,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'authorization_code'
    }

    response = requests.post(token_url, json=token_data)
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        print("Failed to obtain access token:", response.text)
        return None


def get_first_show_id(show_title, access_token):
    """
    Get the ID of the first show matching the title.

    Args:
        show_title (str): Title of the show.
        access_token (str): Access token.

    Returns:
        str: Show ID.
    """
    search_url = f"https://api.trakt.tv/search/show?query={show_title}&type=show"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + access_token,
        "trakt-api-version": "2",
        "trakt-api-key": CLIENT_ID
    }

    response = requests.get(search_url, headers=headers)
    response.raise_for_status()
    show_data = response.json()

    if show_data:
        show_id = show_data[0].get("show", {}).get("ids", {}).get("trakt")
        if show_id:
            return show_id
        else:
            print(f"Error: Failed to get show ID for '{show_title}'.")
            return None
    else:
        print(f"Error: No show found with title '{show_title}'.")
        return None


def get_trakt_episode_id_from_onscreen_value(show_title, onscreen_value, access_token):
    """
    Get Trakt episode ID using onscreen value.

    Args:
        show_title (str): Title of the show.
        onscreen_value (str): Onscreen value.
        access_token (str): Access token.

    Returns:
        dict: Episode data.
    """
    try:
        season_number, episode_number = map(int, onscreen_value[1:].split('E'))

        show_id = get_first_show_id(show_title, access_token)
        if not show_id:
            return None

        episode_summary_url = (f"https://api.trakt.tv/shows/{show_id}/seasons/{season_number}"
                               f"/episodes/{episode_number}?extended=full")
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token,
            "trakt-api-version": "2",
            "trakt-api-key": CLIENT_ID
        }

        response = requests.get(episode_summary_url, headers=headers)
        response.raise_for_status()
        episode_data = response.json()

        return episode_data

    except requests.exceptions.RequestException as e:
        print(f"Error occurred while fetching episode data for '{show_title}': {e}")
        return None
    except ValueError:
        print(f"Error: Invalid onscreen value '{onscreen_value}'.")
        return None


def get_trakt_episode_id(show_title, episode_title, access_token):
    """
    Get Trakt episode ID using show and episode title.

    Args:
        show_title (str): Title of the show.
        episode_title (str): Title of the episode.
        access_token (str): Access token.

    Returns:
        dict: Episode data.
    """
    search_api_url = f"https://api.trakt.tv/search/show?query={show_title}&type=show"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + access_token,
        "trakt-api-version": "2",
        "trakt-api-key": CLIENT_ID
    }
    try:
        response = requests.get(search_api_url, headers=headers)
        response.raise_for_status()
        shows = response.json()
        for show in shows:
            if show["show"]["title"] == show_title:
                show_id = show["show"]["ids"]["trakt"]
                seasons_api_url = f"https://api.trakt.tv/shows/{show_id}/seasons"
                response = requests.get(seasons_api_url, headers=headers)
                response.raise_for_status()
                seasons = response.json()
                for season in seasons:
                    season_number = season["number"]
                    episodes_api_url = f"https://api.trakt.tv/shows/{show_id}/seasons/{season_number}/episodes"
                    response = requests.get(episodes_api_url, headers=headers)
                    response.raise_for_status()
                    episodes = response.json()
                    for episode in episodes:
                        if process.extractOne(episode_title.lower(), [episode["title"].lower()])[1] > 90:
                            return episode
    except requests.exceptions.RequestException as e:
        print(f"Error occurred while fetching episode data for '{show_title}': {e}")
        return None


def create_trakt_list(list_data, access_token):
    """
    Create a Trakt list.

    Args:
        list_data (dict): List data.
        access_token (str): Access token.

    Returns:
        str: List ID.
    """
    create_list_url = "https://api.trakt.tv/users/{}/lists".format(USER_ID)
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + access_token,
        "trakt-api-version": "2",
        "trakt-api-key": CLIENT_ID
    }
    response = requests.post(create_list_url, headers=headers, json=list_data)
    if response.status_code == 201:
        return response.json()["ids"]["trakt"]
    else:
        print("Failed to create Trakt list:", response.text)
        return None


def add_to_trakt_list(list_id, episode_list, access_token):
    """
    Add episodes to a Trakt list.

    Args:
        list_id (str): List ID.
        episode_list (list): List of episodes.
        access_token (str): Access token.

    Returns:
        bool: True if successful, False otherwise.
    """
    add_items_url = "https://api.trakt.tv/users/{}/lists/{}/items".format(USER_ID, list_id)
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + access_token,
        "trakt-api-version": "2",
        "trakt-api-key": CLIENT_ID
    }
    data = {
        "episodes": episode_list
    }
    response = requests.post(add_items_url, headers=headers, json=data)
    if response.status_code == 201:
        print("Episodes added to '{}' list".format(LIST_DATA['name']))
        return True
    else:
        print("Failed to add episode to Trakt list:", response.text)
        return False


def get_authorization_code():
    """
    Get authorization code from the user.

    Returns:
        str: Authorization code.
    """
    print("Please visit the following URL to authorize the application:")
    print(f"https://trakt.tv/oauth/authorize?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}")
    return input("Enter the authorization code from the URL: ")


def main():
    config_file = read_config()
    if config_file is None:
        return

    json_data = read_json_file(config['json_file_name'])
    if json_data is None:
        return
    episodes_list = []

    auth_code = get_authorization_code()
    if auth_code:
        access_token = get_access_token(auth_code)
        if not access_token:
            print("Failed to obtain access token")
            exit()

        list_id = create_trakt_list(config['list_data'], access_token)
        if not list_id:
            print("Failed to create Trakt list")
            exit()

        for program in json_data.get("programs", []):
            show_title = program.get("title", [""])[0].get("value")
            episode_title = program.get("subTitle", [""])[0].get("value")
            onscreen_value = next((item.get("value") for item in program.get("episodeNum", [])
                                   if item.get("system") == "onscreen"), None)

            if show_title and (episode_title or onscreen_value):
                if onscreen_value:
                    episode = get_trakt_episode_id_from_onscreen_value(show_title, onscreen_value, access_token)
                else:
                    episode = get_trakt_episode_id(show_title, episode_title, access_token)

                if episode:
                    episodes_list.append({"ids": episode["ids"]})
                else:
                    print(f"Failed to find Trakt ID for '{episode_title}'")
            else:
                print(f"Empty subtitle or onscreen_value for program: '{show_title}'")

        add_to_trakt_list(list_id, episodes_list, access_token)
    else:
        print("Failed to obtain authorization code")
        exit()


if __name__ == "__main__":
    main()
