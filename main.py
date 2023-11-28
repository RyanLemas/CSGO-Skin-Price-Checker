from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from plyer import notification
import time
import logging

logging.basicConfig(level=logging.INFO)

def show_notification(title, message):
    """
    Displays a notification alert to the user when the item price is equal to or below the desired price

    Args:
        title (str): The title of the notification
        message (str): The message content of the notification
    """
    notification.notify(
        title = title,
        message= message,
        timeout = 10
    )

def conditions(input_condition):
    """
    Determines the users desired condition of the weapon

    Args:
        input_condition (int): value between 1 and 6 representing the desired conditions
            1 - Battle-Scarred
            2 - Well-Worn
            3 - Field-Tested
            4 - Minimal Wear
            5 - Factory New
            6 - if there is no conditon
    
    Returns:
        str: The corrisponding condition as a string
    """

    conditions_dict ={
        1: "Battle-Scarred",
        2: "Well-Worn",
        3: "Field-Tested",
        4: "Minimal Wear",
        5: "Factory New",
        6: "" #no condition
    }
    
    return conditions_dict.get(input_condition, "")

def remove_string(string_value):
    """
    Cleans up the string value so that only the price amount is left

    Args:
        string_value(str): Item price that needs to be cleaned up possible containing $ or USD
    
    Returns:
        str: Price of item without the currency values
    """
    return string_value.replace('$','').replace(' USD','')

def convert_value(string_value,chrome_options):
    """
    Converts the given american currency to canadian currency using XE.com

    Args:
        string_value(str): Item price that needs to be converted from USD to CAD
        chrome_options: Headless browser option

    Returns:
        float: Price of the item in Canadian dollars without the currency values
    """

    # Settting up the Chrome WebDriver with a headless browser and navigate to the XE.com currency converter
    driver_convert = webdriver.Chrome(options = chrome_options)
    driver_convert.get("https://www.xe.com/currencyconverter/convert/?Amount=1&From=USD&To=CAD")

    # Waiting for the conversion input element to be visible then entering the price into the conversion input field
    convert = WebDriverWait(driver_convert, 10).until(
        EC.visibility_of_element_located((By.ID, "amount"))
    )
    value = remove_string(string_value)
    convert.send_keys(value)

    # Waiting for the conversion result to be updated
    element = WebDriverWait(driver_convert,10).until(
        EC.text_to_be_present_in_element((By.XPATH, "//*[@class = 'result__ConvertedText-sc-1bsijpp-0 gpvgZe']"),value)
    )

    # Extracting and rounding converted price
    result = driver_convert.find_element(By.XPATH, "//*[@class = 'result__BigRate-sc-1bsijpp-1 dPdXSB']").text
    converted_price = round(float(result.split()[0]), 2)

    # Closing web driver
    driver_convert.quit()

    return converted_price

def searchCsgoSkins(item_ID,chrome_options):
    """
    Searches the price of item from CSGOskins.gg

    Args:
        item_ID: Item name
        chrome_options: Headless browser option
    Returns:
        converted_price:Cheapest price of the item
        item_site:Site that has the cheapest price
    """
    width = 1200
    height = 800

    # Setting up Chrome WebDriver with provided options
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    driver_csgo_skins = webdriver.Chrome(options = chrome_options)
    driver_csgo_skins.set_window_size(width, height)
    driver_csgo_skins.get("https://csgoskins.gg/")

    # Wait for the search bar to be visible then search for the item
    search_skin = WebDriverWait(driver_csgo_skins,10).until(
        EC.visibility_of_element_located((By.ID, "navbar-search-input"))
    )
    search_skin.send_keys(item_ID)
    search_skin.send_keys(Keys.ENTER)

    # Extracting informations about recommended site and its price
    recommended = WebDriverWait(driver_csgo_skins,5).until(
        EC.visibility_of_element_located((By.XPATH, "//*[@data-template = 'recommended-info']"))
    )
    receommended_site = recommended.find_element(By.XPATH, "./following-sibling::*//*[@class = 'hover:underline']").text
    receommended_price = float(remove_string(recommended.find_element(By.XPATH, "./following-sibling::*//*[contains(text(),'$')]").text))

    # Extracting informations about cheapest site and its price
    cheapest = WebDriverWait(driver_csgo_skins, 10).until(
        EC.presence_of_element_located((By.XPATH, "//div[@class='bg-gray-800 rounded shadow-md relative flex items-center flex-wrap my-4 border-2 border-blue-700 pt-8 pb-4']"))
    )
    cheapest_site = cheapest.find_element(By.XPATH, "./following-sibling::*//*[@class='hover:underline']").text
    cheapest_price = float(remove_string(cheapest.find_element(By.XPATH, "./following-sibling::*//*[contains(text(),'$')]").text))

    # Determining the best price and site
    if cheapest_price < receommended_price:
        item_price = cheapest_price
        item_site = cheapest_site
    else:
        item_price = receommended_price
        item_site = receommended_site

    # Closing web driver
    driver_csgo_skins.quit()

    # Converts cheapest price to canadian dollars
    converted_price = convert_value(str(item_price),chrome_options)

    return converted_price, item_site

def main():
    try:
        # Initializing the CSGO Skin Price Checker
        logging.info("CSGO Skin Price Checker Started")

        # Gathering user inputs for the CSGO item
        item_name = input("Enter Weapon name:")
        item_skin = input("Enter skin name:")
        input_condition = int(input("Enter item condition(1=bs, 2=ww, 3=ft, 4=mw, 5=fn, 6=none):"))
        desired_price = int(input("Desired price to pay:"))

        # Generating the full item name with weapon name, skin name, and condition
        item_condition = conditions(input_condition)
        item = f"{item_name} {item_skin} {item_condition}"

        # Configuring options for the headless Chrome browser
        chrome_options = Options()
        chrome_options.add_argument("--headless")

        # Gathering user input for main loop 
        loops = int(input("How many loops:"))
        runs = int(input("How long of a delay(minutes):"))

        # Main loop for the CSGO Skin Price Checker
        for loop in range(1,loops+1):
            logging.info(f"Loop {loop} of {loops}")

            # Setting up the Chrome browser for the Steam Community Market
            driver_steam = webdriver.Chrome(options=chrome_options)
            driver_steam.get("https://steamcommunity.com/market/")

            # Searching for the specific CSGO item on Steam Community Market
            search_steam = driver_steam.find_element(By.ID,"findItemsSearchBox")
            search_steam.send_keys(item)
            search_steam.send_keys(Keys.ENTER)

            # Waiting for the search result to load
            item_element = WebDriverWait(driver_steam,10).until(
                EC.visibility_of_element_located((By.ID, "result_0"))
            )

            # Extracting the unique ID of the found CSGO item
            item_ID = item_element.get_attribute("data-hash-name")

            # Checking if the item was found on Steam
            if not item_ID or not any(substring in item_ID for substring in item.split()):
                raise ValueError("Steam item not found!")
            
            # Extracting the price of the item on Steam
            steam_price = item_element.find_element(By.XPATH, "//*[@class = 'normal_price']").text
            
            # Converting the Steam price to Canadian dollars
            canadian_price = convert_value(steam_price,chrome_options)
            
            # Searching for the cheapest price and site on CSGOSkins.gg
            cheapest_price, cheapest_site = searchCsgoSkins(item_ID,chrome_options)

            # Calculating the discount between Steam and CSGOSkins prices
            discount = round(canadian_price - cheapest_price, 2)

            #Printing the result message
            output_message = (
                f"Steam Item Name: {item_ID}\n"
                f"Steam price: ${canadian_price} CAD\n"
                f"{cheapest_site} price:${cheapest_price} CAD\n"
                f"Discount: ${discount} CAD"
            )
            print(output_message) 

            # Notifying the user if the cheapest price is below the desired price
            if cheapest_price < desired_price:
                difference = desired_price-cheapest_price
                show_notification(item_ID,f"{item_ID} price is ${cheapest_price} CAD at {cheapest_site}, ${difference} CAD cheaper than the desired price")

            # Delaying before the next loop iteration
            time.sleep(runs*60)

        # Completion message for the CSGO Skin Price Checker
        logging.info("CSGO Skin Price Checker Completed")

    except TimeoutException as te:
        print("TimeoutException: Timed out waiting for page to load")
    except ValueError as ve:
        print(f"ValueError: {ve}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()