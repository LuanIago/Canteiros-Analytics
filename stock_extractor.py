import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
from datetime import datetime
from bs4 import BeautifulSoup

# Project base path
BASE_DIR = Path(__file__).resolve().parent

URL = "http://localhost:7089/"

# Loads the environment variables entered in the file .env
load_dotenv()

# Pulls the data securely (if none exists, sets a blank default value)
USER = os.getenv("POSTO_USER", "")
PASSWORD = os.getenv("POSTO_PASSWORD", "")


def is_report(response):
    """Checks whether the response is the stock report.

    Args:
        response (Response): Playwright response object.

    Returns:
        bool: True if the response contains the stock report, otherwise False.
    """
    if "HandleEvent" not in response.url:
        return False

    try:
        text = response.text()
        return "<!DOCTYPE html>" in text

    except:
        return False


def get_report_html() -> str:
    """Gets the HTML content of the report.

    If USE_MOCK_DATA is True, reads the local TXT file. Otherwise, executes
    the automation of Playwright in localhost.
    """
    use_mock = os.getenv("USE_MOCK_DATA", "False").lower() in ("true", "1")

    if use_mock:
        print("[INFO] Running in MOCK MODE: Reading 'data/report.txt' file...")
        mock_path = BASE_DIR / "data" / "report.txt"

        if not mock_path.exists():
            raise FileNotFoundError(f"Mock file not found in: {mock_path}")

        with open(mock_path, "r", encoding="cp1252") as f:
            return f.read()

    print("[INFO] Running in REAL MODE: Connecting to the server via Playwright...")

    with sync_playwright() as p:
        # Chrome starts visibly to track tests
        browse = p.chromium.launch(headless=False, channel="chrome")
        context = browse.new_context()
        page = context.new_page()

        current_date = datetime.now().strftime("%d%m%Y")

        page.goto(URL)

        # Populating using protected variables and static selectors identified on the login screen
        page.get_by_placeholder("usuário").fill(USER)
        page.get_by_placeholder("senha").fill(PASSWORD)

        # Identify the login button and click on it
        page.get_by_text("Acessar").click()

        print("Successful login (protected credentials)!")

        # Stores the HTML sidebar structure of the gas station system
        side_menu = page.locator('iframe[name="name_htmlMenu_OD7"]').content_frame

        # Go through three menus before accessing the inventory report:
        # [ Relatorios -> Estoques -> Estoques por Grupo ou ]
        menu_reports = side_menu.locator("li").filter(has_text="Relatorios")
        menu_reports.click()

        menu_stocks = menu_reports.get_by_role("link", name="Estoques")
        menu_stocks.click()

        side_menu.get_by_role("link", name="Estoques por Grupo ou").click()

        # Find the date field and fill it in with the current date to receive the current stock
        date_label = page.locator("label.required", has_text="Data do Estoque")
        date_field = date_label.locator("xpath=../following-sibling::div[1]")
        date_field.locator("input").fill(current_date)

        # Select the option to show all products in stock
        page.get_by_role("group", name="Produtos com Estoque").get_by_role(
            "radio", name="Todos"
        ).click()

        # Captures the response of the request after clicking the apply filters button
        with page.expect_response(is_report) as response_info:
            # Click the apply filters button
            page.get_by_role("button", name="Aplicar Filtro").click()

        response = response_info.value
        html_content = response.text()

        browse.close()
        return html_content


def main():

    try:
        # 1. Get the HTML (either from the local TXT or the Playwright)
        raw_html = get_report_html()

        # 2. Treatment of the escape characters of the JavaScript
        clean_html = raw_html.replace(r"\"", '"').replace(r"\n", "\n")
        soup = BeautifulSoup(clean_html, "html.parser")

        # 3. Continues scraping with BeautifulSoup and writes to SQLite
        # ... 

    except Exception as e:
        print(f"\n[ERROR] Execution failed: {e}")
        input("\nPress Enter to close the terminal...")


if __name__ == "__main__":
    main()
