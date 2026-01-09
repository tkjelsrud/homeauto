import requests
import csv
import logging
from io import StringIO

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def get_renovation_costs(csv_url):
    """
    Fetch renovation costs from Google Sheets CSV export.
    Returns dict with categories and costs.
    """
    try:
        response = requests.get(csv_url, timeout=10, allow_redirects=True)
        response.raise_for_status()
        
        # Parse CSV
        csv_data = StringIO(response.text)
        reader = csv.reader(csv_data)
        
        costs = {}
        total = 0
        
        for row in reader:
            # Skip empty rows or headers
            if not row or len(row) < 2:
                continue
            
            category = row[0].strip()
            value_str = row[1].strip()
            
            # Skip if category or value is empty
            if not category or not value_str:
                continue
            
            # Skip header-like rows
            if category.lower() in ['ark for dataeksport', 'kategori', 'category']:
                continue
            
            # Try to parse the value
            try:
                # Remove % sign if present and treat as regular number
                value_str = value_str.replace('%', '').replace(',', '').replace(' ', '')
                value = float(value_str)
                costs[category] = value
                total += value
            except ValueError:
                logging.warning(f"Could not parse value for {category}: {value_str}")
                costs[category] = value_str  # Store as string if not a number
        
        return {
            "categories": costs,
            "total": total,
            "count": len(costs)
        }
        
    except requests.RequestException as e:
        logging.error(f"Failed to fetch renovation costs from {csv_url}: {e}")
        raise
    except Exception as e:
        logging.error(f"Error parsing renovation costs: {e}")
        raise
