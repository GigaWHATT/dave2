# Dave, the MCP Trello Agent
An AI powered Trello Agent that uses MCP to acquire tools. Converse with Dave to create Trello cards, move lists, use labels, and manipulate objects on your Trello board.


---

## Features

Features include:

- Get information on the board (cards, lists, members)
- Manipulate cards (archive, create, restore, move)
- Manipulate lists (move, create)
- Use labels (add labels to cards, filter by label)

---

## Setup
### Cloning the repo
```bash
git clone https://github.com/GigaWHATT/dave2.git
cd dave2
```

### Installing Requirements
```bash
pip install -r requirements.txt
```
or 
```bash
uv add -r requirements.txt
source .venv/Scripts/activate
```

### Setting up environment variables
Create a ```.env``` file with the following content:
```python
TRELLO_API_KEY=790cf33513f03c8187aab39ac2d41d73
TRELLO_API_SECRET=your_trello_api_secret
TRELLO_API_TOKEN=your_trello_api_token
BOARD_ID=your_board_id
```
You may also need your LLM's API key.

To find your Trello API Key, Secret and Token, I invite you to visit: https://altosio.com/trello-migration-guide/.

### Changing the model
Dave's default model is gpt-4o provided by Azure OpenAI. **If you wish to change the model you may need to make significant edits to your MCPClient or provide your own implementation**. You do not have to change the server implementation.

### Run Dave
Once you're all set up, run the client using the following command in your terminal:
```bash
python -m src.main
```
After a moment, a window will appear with a message confirming Dave has connected to the server and collected the tools provided.

---

## Example prompts
Once you've run the ```client.py``` script, you can start entering queries. Here are some examples of what you can ask Dave:
- Create a card called MCP.
- Give the MCP card the AI label.
- Move the Python Packages list to the top.
- Move the Python Packages list in between the Gen AI list and the Docker list (*considering the order of lists on the board*)
- Move the MCP card to the Gen AI list.
- Archive the MCP card. Restore the MCP card
...

---

## Toolshed
Here is an extensive list of Dave's tools:

### List Management

- **get_lists()**  
  Returns all lists on the board.  
  **Returns:** JSON list of lists with their IDs and names.
<br>

- **create_list(list_name: Optional[str] = "New List")**  
  Creates a new list with the given name on the board.  
  **Arguments:**  
  - `list_name` (optional): Name of the new list (default: `"New List"`).  
  **Returns:** JSON of the created list or error message.
<br>

- **move_list(list_name: str, action: str, lower_list: Optional[str] = None, upper_list: Optional[str] = None)**  
  Moves a list to the top, bottom, or between two lists.  
  **Arguments:**  
  - `list_name`: Name of the list to move.  
  - `action`: One of `"top"`, `"bottom"`, or `"between"`.  
  - `lower_list` (optional): Lower bounding list name (required if action is `"between"`).  
  - `upper_list` (optional): Upper bounding list name (required if action is `"between"`).  
  **Returns:** Success message or error.



### Card Management

- **get_cards_short(list_name: Optional[str] = "ALL")**  
  Returns cards in a shortened format (id, name, list) from a specified list or all lists.  
  **Arguments:**  
  - `list_name` (optional): Name of the list or `"ALL"` for all cards (default: `"ALL"`).  
  **Returns:** JSON list of cards.
<br>

- **get_cards_detailed(list_name: Optional[str] = "ALL")**  
  Returns detailed info of cards (id, name, description, labels, URL, list info) from a specified list or all lists.  
  **Arguments:**  
  - `list_name` (optional): Name of the list or `"ALL"` (default: `"ALL"`).  
  **Returns:** JSON list of detailed card info.
<br>

- **create_card(name: Optional[str] = "New Card", list_name: Optional[str] = "Divers", description: Optional[str] = "This card is currently being worked on. Come back later!", labels: Optional[list] = None)**  
  Creates a new card in the specified list with optional description and labels (labels not implemented).  
  **Arguments:**  
  - `name` (optional): Card title (default: `"New Card"`).  
  - `list_name` (optional): Target list name (default: `"Divers"`).  
  - `description` (optional): Card description (default provided).  
  - `labels` (optional): List of labels (currently not implemented).  
  **Returns:** JSON response or error.
<br>

- **add_label(tag_name: str, card_name: str)**  
  Adds a label/tag to a card by their names.  
  **Arguments:**  
  - `tag_name`: Label name.  
  - `card_name`: Card name.  
  **Returns:** JSON response or error.
<br>

- **move_card(card_name: str, list_name: str)**  
  Moves a card to another list.  
  **Arguments:**  
  - `card_name`: Card to move.  
  - `list_name`: Target list.  
  **Returns:** JSON response or error.
<br>

- **archive_card(card_name: str)**  
  Archives the specified card.  
  **Arguments:**  
  - `card_name`: Card to archive.  
  **Returns:** JSON response or error.
<br>

- **get_archived_cards(limit: Optional[int] = 5)**  
  Returns a limited number of most recent archived cards.  
  **Arguments:**  
  - `limit` (optional): Number of cards to return (default: 5).  
  **Returns:** List of archived cards.
<br>

- **restore_card(card_name: str)**  
  Restores the most recently archived card by name and marks it incomplete.  
  **Arguments:**  
  - `card_name`: Card name to restore.  
  **Returns:** JSON response or error.
<br>

- **change_card(card_name: str, new_title: Optional[str] = None, new_description: Optional[str] = None, replace_description: bool = True)**  
  Changes card title and/or description.  
  **Arguments:**  
  - `card_name`: Card to change.  
  - `new_title` (optional): New title.  
  - `new_description` (optional): New description.  
  - `replace_description` (optional): If false, appends description instead of replacing (default: True).  
  **Returns:** None or error string.
<br>

- **filter_by_label(label_name: str)**  
  Returns a list of card names filtered by label.  
  **Arguments:**  
  - `label_name`: Label to filter by.  
  **Returns:** List of card names.


### Board Metadata

- **get_members()**  
  Returns the members of the board.  
  **Returns:** JSON list of board members or error.

---

## Extending Dave
If you'd like, you can add your own tools to Dave's toolshed in the ```client.py``` file! You can also use Dave for other Trello boards, simply by changing the ```BOARD_ID```and ```BOARD_NAME```in your ```.env``` file.

---

## Contact
In case of any problems, feel free to open an issue at: https://github.com/GigaWHATT/dave2/issues.

