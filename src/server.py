# ---------IMPORTS---------

import os
from typing import Optional
from loguru import logger
import json
import asyncio
import requests

from trello import TrelloClient

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from zoneinfo import ZoneInfo


# ----------INIT------------

mcp = FastMCP("dave")

load_dotenv()

# BOARD_ID = "JDtNhDSs"
BOARD_ID = os.getenv('BOARD_ID')
BOARD_NAME = os.getenv('BOARD_NAME')


client = TrelloClient(
    api_key=os.getenv("TRELLO_API_KEY"),
    api_secret=os.getenv("TRELLO_API_SECRET"),
    token=os.getenv("TRELLO_API_TOKEN")
)


# ---------FUNCTIONS----------

def format_card(card, trello_list) -> dict:
    return {
        'id': card.id,
        'name': card.name,
        'description': card.description,
        'labels': [label.name for label in card.labels],
        'url': card.short_url,
        'list': {
            'list_id': trello_list.id,
            'list_name': trello_list.name
        }
    }


def get_card_by_name(card_name: str):
    return next((card for card in board.open_cards() if card.name.lower() == card_name.lower()), None)


def get_list_by_name(list_name: str):
    return next((trello_list for trello_list in board.open_lists() if trello_list.name.lower() == list_name.lower()), None)


def get_label_by_name(label_name: str):
    return next((label for label in board.get_labels() if label.name.lower() == label_name.lower()), None)


# -----------TOOLS-----------


# -----------LIST MANIP------------
@mcp.tool()
async def get_lists() -> list:
    """Returns the lists of the board

    Returns:
        list: json dump of lists 
    """
    try:
        lists = board.open_lists()
        return json.dumps([{'id': lst.id, 'name': lst.name} for lst in lists])
    except Exception as e:
        print(f"Error: {e}")
        return [e]


@mcp.tool()
async def create_list(list_name: Optional[str] = "New List") -> dict:
    """ [consent] Creates a list

    Args:
        list_name (Optional[str], optional): name of list. Defaults to "New List".

    Returns:
        dict : JSON response of created list or error
    """
    try:
        url = f"https://api.trello.com/1/lists"

        query = {
            'key': os.getenv('TRELLO_API_KEY'),
            'token': os.getenv('TRELLO_API_TOKEN'),
            'idBoard': BOARD_ID,
            'name': list_name
        }

        response = requests.post(url, data=query)

        if response.status_code != 200:
            return response.text

        return response.json()

    except Exception as e:
        print(f"Error: {e}")
        return e


@mcp.tool()
async def move_list(list_name: str, action: str, lower_list: Optional[str] = None, upper_list: Optional[str] = None) -> str:
    """ [consent] Moves a list to the bottom, the top, or in between two lists.

    Args:
        list_name (str): name of list to move
        action (str): an action in the list ['top','bottom',between']
        lower_list (Optional[str], optional): lower bounding list to the moving list. Defaults to None.
        upper_list (Optional[str], optional): upper bounding list to the moving list. Defaults to None.

    Returns:
        str: None or error
    """
    try:
        moving_list = get_list_by_name(list_name)

        if action in ["top", "bottom"]:
            moving_list.set_pos(action)
            return "Successfully moved list."
        elif action == "between":
            if lower_list and upper_list:
                lower_pos = get_list_by_name(lower_list).pos
                upper_pos = get_list_by_name(upper_list).pos
            else:
                return "A boundary list was not given."
            moving_list.set_pos((lower_pos+upper_pos)/2)
            return "Successfully moved list."
        else:
            return "Invalid action selected by LLM, action can only be 'top','bottom','between'."
    except Exception as e:
        print(f"Error: {e}")
        return e


# -----------CARD MANIP------------

@mcp.tool()
async def get_cards_short(list_name: Optional[str] = "ALL") -> list:
    """ Returns cards of a given board or all cards of the board in a shortened format

    Args:
        list_name (Optional[str], optional): name of list to get cards from. Defaults to "ALL".

    Returns:
        list: json dump of card list, with each card's id, name and list
    """
    try:
        result = []
        lists = board.list_lists()
        if list_name == "ALL":
            for trello_list in lists:
                cards = trello_list.list_cards()
                for card in cards:
                    result.append({'id': card.id, 'name': card.name, 'list': {
                                'list_id': trello_list.id, 'list_name': trello_list.name}})
        else:
            trello_list = get_list_by_name(list_name)
            cards = trello_list.list_cards()
            for card in cards:
                result.append([{'id': card.id, 'name': card.name, 'list': {
                            'list_id': trello_list.id, 'list_name': trello_list.name}}])
        return json.dumps(result)
    except Exception as e:
        print(f"Error: {e}")
        return [e]


@mcp.tool()
async def get_cards_detailed(list_name: Optional[str] = "ALL") -> list:
    """ Returns cards of a given board or all cards of the board in a detailed format

    Args:
        list_name (Optional[str], optional): name of list to get cards from. Defaults to "ALL".

    Returns:
        list: json dump of card list, with each card's id, name, description, labels, url, and list
    """
    try:
        result = []
        lists = board.list_lists()
        if list_name == "ALL":
            for trello_list in lists:
                cards = trello_list.list_cards()
                for card in cards:
                    result.append(format_card(card, trello_list))
        else:
            trello_list = get_list_by_name(list_name)
            cards = trello_list.list_cards()
            for card in cards:
                result.append([format_card(card, trello_list)])
        return json.dumps(result)
    except Exception as e:
        print(f"Error: {e}")
        return [e]


@mcp.tool()
async def create_card(name: Optional[str] = "New Card", list_name: Optional[str] = "Divers", description: Optional[str] = "This card is currently being worked on. Come back later!", labels: Optional[list] = None) -> dict:
    """ [consent] Creates a card

    Args:
        name (Optional[str], optional): name of the card. Defaults to "New Card".
        list_name (Optional[str], optional): name of the list in which the card will reside. Defaults to "Divers".
        description (Optional[str], optional): contents of the card. Defaults to "This card is currently being worked on. Come back later!".
        labels (Optional[list], optional): labels of the card (not implemented). Defaults to None.

    Returns:
        dict: JSON response or error
    """
    id_list = get_list_by_name(list_name).id
    url = "https://api.trello.com/1/cards"
    query = {
        'key': os.getenv("TRELLO_API_KEY"),
        'token': os.getenv("TRELLO_API_TOKEN"),
        'idList': id_list,
        'name': name,
        'desc': description
    }
    try:
        response = requests.post(url, params=query)

        if response.status_code != 200:
            return response.text

        return response.json()
    except Exception as e:
        print(e)
        return {"error": str(e)}


@mcp.tool()
async def return_labels() -> list:
    """ Returns the board's labels/tags

    Returns:
        list: board's tags
    """
    try:
        return board.get_labels()
    except Exception as e:
        print(f"Error: {e}")
        return [e]


@mcp.tool()
async def add_label(tag_name: str, card_name: str) -> dict:
    """ [consent] Adds a label or a tag to a given card.

    Args:
        tag_name (str): user given name of the label to give to card
        card_name (str): name of card getting tagged

    Returns:
        dict: JSON response or error

    """
    try:
        card_id = get_card_by_name(card_name).id
        label_id = get_label_by_name(tag_name).id
        url = f"https://api.trello.com/1/cards/{card_id}/idLabels"
        query = {
            'key': os.getenv("TRELLO_API_KEY"),
            'token': os.getenv("TRELLO_API_TOKEN"),
            'value': label_id
        }

        response = requests.post(url, params=query)

        if response.status_code != 200:
            return response.text

        return response.json()

    except Exception as e:
        print(f"Error {e}")
        return {"error": str(e)}


@mcp.tool()
async def move_card(card_name: str, list_name: str) -> dict:
    """ [consent] Move a card to another list

    Args:
        card_name (str): name of card to move
        list_name (str): name of target list to move card to

    Returns:
        dict: JSON response or error
    """
    try:
        card_id = get_card_by_name(card_name).id
        list_id = get_list_by_name(list_name).id

        url = f"https://api.trello.com/1/cards/{card_id}"
        query = {
            'key': os.getenv("TRELLO_API_KEY"),
            'token': os.getenv("TRELLO_API_TOKEN"),
            'idList': list_id
        }

        response = requests.put(url, params=query)

        if response.status_code != 200:
            return response.text

        return response.json()

    except Exception as e:
        print(f"Error {e}")
        return {"error": str(e)}


@mcp.tool()
async def archive_card(card_name: str) -> dict:
    """ [consent] Archives a card

    Args:
        card_name (str): name of card to archive

    Returns:
        dict: JSON response or error
    """
    try:
        card_id = get_card_by_name(card_name).id

        url = f"https://api.trello.com/1/cards/{card_id}"
        query = {
            'key': os.getenv("TRELLO_API_KEY"),
            'token': os.getenv("TRELLO_API_TOKEN"),
            'closed': 'true'
        }

        response = requests.put(url, params=query)

        if response.status_code != 200:
            logger.info("In error of response.")
            return response.text

        # return response.json()

    except Exception as e:
        print(f"Error {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_archived_cards(limit: Optional[int] = 5) -> list:
    """ Returns limit number of the last archived cards

    Args:
        limit (int, optional): threshold of cards to return. Defaults to 5.

    Returns:
        list: list of limit number of last archived cards
    """
    try:
        archived_cards = board.closed_cards()
        return archived_cards[:limit]
    except Exception as e:
        print(f"Error: {e}")
        return [e]


@mcp.tool()
async def restore_card(card_name: str) -> dict:
    """ [consent] Restores archived card with name: card_name and marks it as incomplete. In the case of multiple cards with the same name in archives, restores the most recently archived card.

    Args:
        card_name (str): name of the card to restore from archive

    Returns:
        dict: JSON response or error
    """
    try:
        card_id = next((card for card in board.closed_cards()
                    if card.name.lower() == card_name.lower()), None).id

        url = f"https://api.trello.com/1/cards/{card_id}"
        query = {
            'key': os.getenv("TRELLO_API_KEY"),
            'token': os.getenv("TRELLO_API_TOKEN"),
            'closed': 'false',
            'state': 'incomplete'
        }

        response = requests.put(url, params=query)

        if response.status_code != 200:
            logger.info("In error of response.")
            return response.text

        return response.json()

    except Exception as e:
        print(f"Error {e}")
        return {"error": str(e)}


@mcp.tool()
async def change_card(card_name: str, new_title: Optional[str] = None, new_description: Optional[str] = None, replace_description: bool = True) -> str:
    """ [consent] Changes card title and/or description

    Args:
        card_name (str): name of card to change
        new_title (Optional[str], optional): new title to give to card. Defaults to None.
        new_description (Optional[str], optional): new description to give to card. Defaults to None.
        replace_description (bool, optional): does the new description replace the old one?. Defaults to True.

    Returns:
        str : returns success message or error
    """
    try:
        card = get_card_by_name(card_name)
        if new_title != None:
            card.set_name(new_title)
        if new_description != None:
            if replace_description == False:
                current = card.desc
                new = current+" "+new_description
                card.set_description(new)
            else:
                card.set_description(new_description)
        return "The card has been successfully changed."
    except Exception as e:
        print(f"Error: {e}")
        return e


@mcp.tool()
async def filter_by_label(label_name: str) -> list:
    """ Filter all cards by a label

    Args:
        label_name (str): name of label to filter by

    Returns:
        list: cards with the given label
    """
    cards = board.get_cards('open')
    label_id = get_label_by_name(label_name).id
    filtered = [card.name for card in cards if label_id in card.idLabels]

    return filtered


# ---------META DATA---------

@mcp.tool()
async def get_members() -> dict:
    """ Returns the members of the board

    Returns:
        dict: JSON response or error
    """
    try:

        url = f"https://api.trello.com/1/boards/{BOARD_ID}/members"
        query = {
            'key': os.getenv('TRELLO_API_KEY'),
            'token': os.getenv('TRELLO_API_TOKEN')
        }

        response = requests.get(url, params=query)

        if response.status_code != 200:
            return response.text

        return response.json()

    except Exception as e:
        print(f"Error: {e}")
        return {"error": str(e)}


# ----------RUN-----------

if __name__ == "__main__":
    board = client.get_board(BOARD_ID)
    mcp.run()


# TODO: ----------NEW FUNC--------------
# TODO: archive list functionality??
# TODO: restore list from archives??
# TODO: extension VScode
# TODO: francais

# TODO: ----------FIXES-------------

# TODO: ----------OPTIM-------------
# TODO: make the LLM 'autocomplete' list names in case of typo --> I think it already does that --> it autocompletes but does not correct typos

# TODO: ----------DOCS--------------
# TODO: Make a README.md
