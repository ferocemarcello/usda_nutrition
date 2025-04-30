import requests
import time
import json
def fetch_food_list(api_key, page_number=1, page_size=100, max_retries=3):
    """Fetches a list of foods from the USDA FoodData Central API."""
    url = f"https://api.nal.usda.gov/fdc/v1/foods/list?api_key={api_key}&pageNumber={page_number}&pageSize={page_size}"
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 500:
                try:
                    error_json = response.json()
                    if "message" in error_json and "all shards failed" in error_json["message"]:
                        return "all_shards_failed"
                except json.JSONDecodeError:
                    pass
                retries += 1
                wait_time = 2 ** retries
                print(f"Server error (500) fetching food list (page {page_number}). Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise
        except requests.exceptions.RequestException as e:
            print(f"Error fetching food list (page {page_number}): {e}")
            return None
        return response.json()
    print(f"Max retries reached for fetching food list (page {page_number}).")
    return None

def main_method(api_key):
    """Fetches food data and nutrient information and saves it to an Excel file.
    Only processes foods with FDC IDs greater than start_fdc_id.  Appends to existing file."""

    page_number = 1
    all_food_list = []
    while True:
        food_list_response:dict = fetch_food_list(api_key, page_number)
        if isinstance(food_list_response, str) and str.__eq__(food_list_response, "all_shards_failed"):
            break
        all_food_list.extend(food_list_response)
        page_number += 1
        time.sleep(0.1)
    print(f"len(all_food_list): {len(all_food_list)}")
    food_ids = sorted([{"fdcId":x['fdcId'], "description":x['description']} for x in all_food_list], key=lambda item: item["description"])
    output_filename = "food_ids.json"

    # Save the list of dictionaries to a JSON file
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(food_ids, f, indent=4, ensure_ascii=False)
        print(f"Successfully saved food IDs and descriptions to {output_filename}")
    except IOError as e:
        print(f"Error saving data to {output_filename}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while saving: {e}")

if __name__ == "__main__":
    api_key = ""
    # Replace with the list of nutrient IDs you retrieved
    main_method(api_key)
