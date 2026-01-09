import requests
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def get_trello_tasks(api_key, token, board_id, list_name="I arbeid"):
    """
    Fetch tasks from a specific Trello list.
    Returns list of tasks with name, labels, and due date.
    """
    try:
        # First, get all lists on the board
        lists_url = f"https://api.trello.com/1/boards/{board_id}/lists"
        params = {
            "key": api_key,
            "token": token,
            "fields": "name,id"
        }
        
        response = requests.get(lists_url, params=params, timeout=10)
        response.raise_for_status()
        lists = response.json()
        
        # Find the target list
        target_list_id = None
        for lst in lists:
            if lst["name"] == list_name:
                target_list_id = lst["id"]
                break
        
        if not target_list_id:
            logging.warning(f"List '{list_name}' not found on board")
            return []
        
        # Get cards from the target list
        cards_url = f"https://api.trello.com/1/lists/{target_list_id}/cards"
        params = {
            "key": api_key,
            "token": token,
            "fields": "name,labels,due,desc"
        }
        
        response = requests.get(cards_url, params=params, timeout=10)
        response.raise_for_status()
        cards = response.json()
        
        # Format the tasks
        tasks = []
        for card in cards:
            label_names = [label["name"] for label in card.get("labels", []) if label.get("name")]
            
            tasks.append({
                "name": card["name"],
                "labels": label_names,
                "due": card.get("due"),
                "description": card.get("desc", "")
            })
        
        return tasks
        
    except requests.RequestException as e:
        logging.error(f"Failed to fetch Trello tasks: {e}")
        raise
    except Exception as e:
        logging.error(f"Error processing Trello data: {e}")
        raise
