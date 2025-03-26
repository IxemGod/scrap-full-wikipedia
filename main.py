import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import cssutils

# Wikipedia page do downloads
title = "Python_(langage)"
base_url = "https://fr.wikipedia.org"
url = f"{base_url}/wiki/{title}"
headers = {"User-Agent": "Mozilla/5.0"}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    page_text = response.text
    with open(f"src/page/{title}.html", "w+", encoding="utf-8") as f:
        f.write(page_text)
    print("Page Wikipedia téléchargée avec succès.")

     # Parse html with BeautifulSoup
    soup = BeautifulSoup(page_text, "html.parser")

    # Find all links to stylesheets
    stylesheets = soup.find_all("link", {"rel": "stylesheet"})

    # Set a number that will be increment to the number of styles files
    nbr_style_file = 0


    # Extrat and print the complete urls
    for sheet in stylesheets:
        href = sheet.get("href")
        if href:
            # On incrémente de 1
            nbr_style_file = nbr_style_file + 1

            full_url = urljoin(base_url, href)  # Convert to absolute URL
            print("Stylesheet trouvé :", full_url)
            # On télécharge le fichier css
            response_style = requests.get(full_url, headers=headers)

            raw_css = response_style.text

            # Parse and formate css
            css_parser = cssutils.parseString(raw_css)
            formatted_css = css_parser.cssText.decode("utf-8")

            with open(f"src/css/{title}{nbr_style_file}.css", "w+", encoding="utf-8") as f:
                f.write(formatted_css)
                f.close()

            # Add a tag link in the page
            f_current_page = open(f"src/page/{title}.html","w+")
            page_text = f'<link rel="stylesheet" href="../css/{title}{nbr_style_file}.css">'+page_text
            content_current_page = f_current_page.write(page_text)
            f_current_page.close()



else:
    print(f"Erreur {response.status_code} en récupérant la page")
