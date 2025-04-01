import requests
import openpyxl
import json

def fetch_food_data(api_key, page_number=1, page_size=50, max_retries=5):
    """Fetches food data with exponential backoff."""
    url = f"https://api.nal.usda.gov/fdc/v1/foods/list?api_key={api_key}&pageNumber={page_number}&pageSize={page_size}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 500:
            try:
                error_json = response.json()
                if "message" in error_json and "all shards failed" in error_json["message"]:
                    return "all_shards_failed" #return a specific string to be handled later.
            except json.JSONDecodeError:
                pass #if not json, ignore
            print(f"Server error (500). Retrying in {wait_time} seconds...")
        else:
            raise #reraise other errors
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None
    print("Max retries reached. Unable to fetch data.")
    return None

def extract_unique_nutrients(api_key, output_filename="nutrient_list.xlsx"):
    """Extracts and prints unique nutrient names and their IDs."""
    page_number = 1
    unique_nutrients = {}

    while True:
        print(f"in page number {page_number}")
        food_data = fetch_food_data(api_key, page_number)
        if food_data is None or not food_data:
            break
        if food_data == "all_shards_failed":
            print("all shards failed. Saving progress...")
            break #stop the loop, save the xlsx

        for food in food_data:
            if "foodNutrients" in food:
                for nutrient in food["foodNutrients"]:
                    nutrient_name = nutrient.get("name", "None")
                    nutrient_number = nutrient.get("number", "None")
                    if nutrient_name != "None" and nutrient_number != "None" and nutrient_name not in unique_nutrients:
                        unique_nutrients[nutrient_name] = nutrient_number
        page_number += 1

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(["Nutrient Name", "Nutrient Number"])

    for nutrient_name, nutrient_number in unique_nutrients.items():
        sheet.append([nutrient_name, nutrient_number])
    
    workbook.save(output_filename)

api_key = "Your Api Key"
extract_unique_nutrients(api_key)
