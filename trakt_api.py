import json
import requests
from fuzzywuzzy import process
from itertools import chain


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


def is_movie(program):
    """
    Check if the program is a movie.

    Args:
        program (dict): Program data.

    Returns:
        bool: True if the program is a movie, False otherwise.
    """
    for episode_key in ["episodeNum", "episodenum"]:
        for episode in program.get(episode_key, []):
            if episode.get("system") == "dd_progid":
                value = episode.get("value", "")
                if value[:2].lower() == "mv":
                    return True
    return False


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


def search_episode_by_onscreen_value(show_title, onscreen_value, access_token):
    """
    Get Trakt episode ID using onscreen value.

    Args:
        show_title (str): Title of the show.
        onscreen_value (str): Onscreen value.
        access_token (str): Access token.

    Returns:
        dict: Episode data if found, None otherwise.
    """
    season_number = ""
    episode_number = ""
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
        if response.status_code == 404:
            return None  # Episode not found
        response.raise_for_status()
        episode_data = response.json()

        return episode_data

    except requests.exceptions.RequestException as e:
        print(f"Error occurred while fetching S{season_number}E{episode_number} data in '{show_title}': {e}")
        return None
    except ValueError:
        print(f"Error: Invalid onscreen value '{onscreen_value}'.")
        return None


def search_episode_by_title(show_title, episode_title, access_token):
    """
    Search for a specific episode by its title.

    Args:
        show_title (str): Title of the show.
        episode_title (str): Title of the episode.
        access_token (str): Access token.

    Returns:
        dict: Episode data if found, None otherwise.
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
            if process.extractOne(show_title.lower(), [show["show"]["title"].lower()])[1] > 90:
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


def search_movie_by_title_and_year(movie_title, movie_year, access_token):
    """
    Search for a movie by its title and release year.

    Args:
        movie_title (str): Title of the movie.
        movie_year (str): Release year of the movie.
        access_token (str): Access token.

    Returns:
        dict: Movie data if found, None otherwise.
    """
    search_api_url = f"https://api.trakt.tv/search/movie?query={movie_title}&type=movie"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + access_token,
        "trakt-api-version": "2",
        "trakt-api-key": CLIENT_ID
    }
    try:
        response = requests.get(search_api_url, headers=headers)
        response.raise_for_status()
        movie_data = response.json()
        if movie_data:
            for movie in movie_data:
                movie_info = movie['movie']
                if movie_info['year'] == int(movie_year):
                    return movie_info
            print(f"Failed to find Trakt ID of the movie '{movie_title}' for the year '{movie_year}'")
            return None
        else:
            print(f"Failed to find Trakt ID of the movie '{movie_title}'-'{movie_year}'")
            return None
    except requests.RequestException as e:
        print(f"Error fetching movie data of '{movie_title}'-'{movie_year}':", {e})
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


def add_to_trakt_list(list_id, movie_list, episode_list, access_token):
    """
    Add episodes to a Trakt list.

    Args:
        list_id (str): List ID.
        movie_list (list): List of movie data to be added.
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
        "movies": movie_list,
        "episodes": episode_list
    }
    response = requests.post(add_items_url, headers=headers, json=data)
    if response.status_code == 201:
        print("shows/movies added to '{}' Trakt list".format(LIST_DATA['name']))
        return True
    else:
        print("Failed to add shows/movies to '{}' Trakt list:".format(LIST_DATA['name']))
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


def get_trakt_episode_data(show_title, episode_title, onscreen_value, access_token):
    """
    Get Trakt episode data.

    Args:
        show_title (str): Title of the show.
        episode_title (str): Title of the episode.
        onscreen_value (str): Onscreen value.
        access_token (str): Access token.

    Returns:
        list: List of episode data.
    """
    episodes_list = []
    if show_title and (episode_title or onscreen_value):
        if onscreen_value:
            episode = search_episode_by_onscreen_value(show_title, onscreen_value, access_token)
            if not episode:
                episode = search_episode_by_title(show_title, episode_title, access_token)
                if episode:
                    episodes_list.append({"ids": episode["ids"]})
                else:
                    print(f"'{onscreen_value}' in '{show_title}' not found")
        else:
            episode = search_episode_by_title(show_title, episode_title, access_token)
            if (not episode) and (';' in episode_title):
                episode_titles = episode_title.split(';')
                for short_episode in episode_titles:
                    episode = search_episode_by_title(show_title, short_episode.strip(), access_token)
                    if episode:
                        episodes_list.append({"ids": episode["ids"]})
                    else:
                        print(f"Failed to find Trakt ID for '{short_episode.strip()}' in '{show_title}'")

        if episode:
            episodes_list.append({"ids": episode["ids"]})
        elif (not episode) and not (';' in episode_title):
            print(f"Failed to find Trakt ID for '{episode_title}' in '{show_title}'")
        return episodes_list
    else:
        print(f"Empty subtitle or onscreen_value for program: '{show_title}'")

    return episodes_list


def main():
    """
    Main function to orchestrate the Trakt list creation and data addition process.
    """
    json_data = read_json_file(config['json_file_name'])
    movie_payload = []
    episodes_payload = []
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
            if is_movie(program):
                movie_title = program["title"][0]["value"] if program.get("title") else None
                movie_year = program["date"] if program.get("date") else None
                if movie_title and movie_year:
                    movie_data = search_movie_by_title_and_year(movie_title.strip(), movie_year, access_token)
                    if movie_data:
                        movie_payload.append({"ids": movie_data["ids"]})
                else:
                    print(f"Both movie title and year are required to search for movie data of '{movie_title}'.")
            else:
                show_title = program["title"][0]["value"] if program.get("title") else None
                episode_title = ""
                # Check if "subTitle" or "subtitle" exists
                if "subTitle" in program:
                    episode_title = program.get("subTitle", [""])[0].get("value") if program.get("subTitle") else None
                elif "subtitle" in program:
                    episode_title = program.get("subtitle", [""])[0].get("value") if program.get("subtitle") else None
                onscreen_value = next((item.get("value") for item in program.get("episodeNum", [])
                                       if item.get("system") == "onscreen"), None)
                episodes_list = get_trakt_episode_data(show_title, episode_title, onscreen_value, access_token)
                episodes_payload.append(episodes_list)

        # Flatten the episodes_payload list
        episodes_payload = list(chain.from_iterable(episodes_payload))
        add_to_trakt_list(list_id, movie_payload, episodes_payload, access_token)
    else:
        print("Failed to obtain authorization code")
        exit()


if __name__ == "__main__":
    main()
