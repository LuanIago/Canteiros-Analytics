import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
from datetime import datetime
from bs4 import BeautifulSoup
import sqlite3

# Project base path
BASE_DIR = Path(__file__).resolve().parent

# Loads the environment variables entered in the file .env
load_dotenv()

URL = os.getenv("URL", "")
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
        # Get the HTML (either from the local TXT or the Playwright)
        raw_html = get_report_html()

        # Treatment of the escape characters of the JavaScript
        clean_html = raw_html.replace(r"\"", '"').replace(r"\n", "\n")
        soup = BeautifulSoup(clean_html, "html.parser")
        body = soup.find("body")

        # Groups all products by category in a list
        tables_by_category = body.find_all("div", class_="table-wrapper")

        products_updated = []

        for table in tables_by_category:
            # Captures and clears the category name (ex: "ADITIVOS", "COMBUSTIVEIS")
            category = table.find("table").find("tr").find("th").text.strip()

            # Locates the tbody containing the products of the identified category
            tbody = table.find("table", class_="fl-table").find("tbody")
            tbody_prod = tbody.find_all("tr")

            for tr in tbody_prod:
                prod_info = tr.find_all("td")

                # Prevents blank or incorrect header lines
                if not prod_info or len(prod_info) < 5:
                    continue

                prod_code = prod_info[0].text.split("-", 1)[0].strip()
                prod_name = prod_info[0].text.split("-", 1)[1].strip()

                raw_stock_qt = (
                    prod_info[1].text.strip().replace(".", "").replace(",", ".")
                )
                stock_qt = float(raw_stock_qt) if raw_stock_qt else 0.0

                # Prices: remove 'R$', remove one thousand point and exchange comma per point
                raw_buy = (
                    prod_info[2]
                    .text.replace("R$", "")
                    .strip()
                    .replace(".", "")
                    .replace(",", ".")
                )
                raw_sell = (
                    prod_info[4]
                    .text.replace("R$", "")
                    .strip()
                    .replace(".", "")
                    .replace(",", ".")
                )

                buying_price = float(raw_buy) if raw_buy else 0.0
                selling_price = float(raw_sell) if raw_sell else 0.0

                products_updated.append(
                    {
                        "codigo": prod_code,
                        "nome": prod_name,
                        "categoria": category,
                        "qt_estoque": stock_qt,
                        "preco_venda": selling_price,
                        "preco_compra": buying_price,
                    }
                )

            # Transfers collected data to the 'stock_products.db' database
            connection = sqlite3.connect("data/stock_products.db")
            cursor = connection.cursor()

    except Exception as e:
        print(f"\n[ERROR] Execution failed: {e}")
        input("\nPress Enter to close the terminal...")


if __name__ == "__main__":
    main()
