import requests
import openpyxl
import time
import json

FOOD_NUTRIENTS_KEY = "foodNutrients"
def fetch_food_list(api_key, page_number=1, page_size=50, max_retries=3):
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

def fetch_food_details(api_key, fdc_id, nutrient_ids, max_retries=3):
    """Fetches detailed nutrient information for a specific food."""
    url = f"https://api.nal.usda.gov/fdc/v1/food/{fdc_id}?api_key={api_key}&nutrients={','.join(map(str, nutrient_ids))}"
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"Food with FDC ID {fdc_id} not found.")
                return None
            elif e.response.status_code == 500:
                retries += 1
                wait_time = 2 ** retries
                print(f"Server error (500) fetching details for FDC ID {fdc_id}. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise
        except requests.exceptions.RequestException as e:
            print(f"Error fetching details for FDC ID {fdc_id}: {e}")
            return None
        return response.json()
    print(f"Max retries reached for fetching details for FDC ID {fdc_id}.")
    return None

def main_method(api_key, nutrient_ids, output_filename="food_nutrition_data.xlsx"):
    """Fetches food data and nutrient information and saves it to an Excel file."""
    page_number = 1
    progress_counter = 0
    save_interval = 50  # Save progress every N foods

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    header = ["fdcId", "description"] + [f"Nutrient ID {nid}" for nid in nutrient_ids]
    sheet.append(header)

    while True:
        food_list_response:dict = fetch_food_list(api_key, page_number)

        if food_list_response is None:
            print("Failed to retrieve food list. Exiting.")
            break
        elif food_list_response == "all_shards_failed":
            print("Error: 'all shards failed' while fetching food list. Saving progress...")
            break
        elif not food_list_response:
            print("No more food items found in the list.")
            break

        if not food_list_response:
            print("No foods found on this page.")
            break

        for food in food_list_response:
            fdc_id = food.get("fdcId")
            description = food.get("description", "N/A")
            if fdc_id:
                food_details = fetch_food_details(api_key, fdc_id, nutrient_ids)
                if food_details and FOOD_NUTRIENTS_KEY in food_details and food_details[FOOD_NUTRIENTS_KEY]:
                    row_data = [fdc_id, description]
                    food_values = food_details[FOOD_NUTRIENTS_KEY]
                    food_nutrients = [{"nutrient": x["nutrient"], "amount": x["amount"]} for x in food_values]
                    nutrient_list = []
                    for nutrient in food_nutrients:
                        nutrient_number = float(nutrient["nutrient"]["number"])
                        if nutrient_number in nutrient_ids:
                            nutrient_list.append({'nutrient number': nutrient_number, 'nutrient name': nutrient["nutrient"]["name"], 'unit_name':nutrient["nutrient"]["unitName"], 'amount': nutrient["amount"]})
                    if nutrient_list:
                        to_append = {'nutrients': nutrient_list}
                        row_data.append(to_append)
                        row_data_list = [row_data[0], row_data[1]]
                        for nutrient_info in row_data[2]["nutrients"]:
                            for nutrient_val in nutrient_info.values():
                                row_data_list.append(nutrient_val)
                        sheet.append(row_data_list)
                    progress_counter += 1
                    if progress_counter % save_interval == 0:
                        print(f"Processed {progress_counter} foods. Saving progress...")
                        try:
                            workbook.save(output_filename)
                        except Exception as e:
                            print(f"Error saving workbook: {e}")

        page_number += 1
        time.sleep(0.1)

    try:
        workbook.save(output_filename)
        print(f"Successfully saved data for {progress_counter} foods to {output_filename}")
    except Exception as e:
        print(f"Error saving final workbook: {e}")

if __name__ == "__main__":
    api_key = ""
    # Replace with the list of nutrient IDs you retrieved
    nutrient_ids_to_fetch = [203, 204, 205, 208,269,291,601,606,645,646,605,210,211,214,212,213,287,957,958,269.3,298,693,695,205.2,293]
    main_method(api_key, nutrient_ids_to_fetch)
