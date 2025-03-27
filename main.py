import requests
from bs4 import BeautifulSoup, Comment
from urllib.parse import urljoin
import cssutils
import logging
import os

# Desactivate warnings of cssutils
cssutils.log.setLevel(logging.CRITICAL)

def part_clean(content):
    global class_list_to_delete, id_list_to_delete
    soup_clean = BeautifulSoup(content, "html.parser")

    for class_item in class_list_to_delete:
        for element in soup_clean.find_all(class_=class_item):
            element.decompose()  # Delete class tag

    for id_item in id_list_to_delete:
        element = soup_clean.find(id=id_item)
        element.decompose()  # delete id tag

    for script in soup_clean.find_all("script"):
        script.decompose()  # delete script tag

    # Supprimer tous les commentaires
    for comment in soup_clean.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()  # Delete comments

    return soup_clean.prettify()

def download_style(page_text, title, base_url):
    global headers
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
            # Download the css file
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
    return page_text

def download_images(page_text, title, base_url):
    global headers
    # Parse html with BeautifulSoup
    soup = BeautifulSoup(page_text, "html.parser")
    # Find all img
    images = soup.find_all("img")
    # Set a number that will be increment to the number of styles files
    nbr_img_file = 0
    # Extrat and print the complete urls
    for img in images:
        src = img.get("src")
        if src:
            # On incrémente de 1
            nbr_img_file = nbr_img_file + 1
            full_url = urljoin(base_url, src)  # Convert to absolute URL
            # Download the image file
            if(full_url != "https://login.wikimedia.org/wiki/Special:CentralAutoLogin/start?useformat=desktop&type=1x1&usesul3=0"):
                response_img = requests.get(full_url, headers=headers)
                if response_img.status_code == 200:
                    img_ext = full_url.split(".")[-1]  # Retrieve the image extension
                    img_path = f"src/assets/images/{title}_{nbr_img_file}.{img_ext}"
                    with open(img_path, "wb+") as f:
                        f.write(response_img.content)
                    
                    # Change the `src` attribute to point to the local file
                    img["src"] = f"../assets/images/{title}_{nbr_img_file}.{img_ext}"
                    img["srcset"] = f"../assets/images/{title}_{nbr_img_file}.{img_ext}"

                    wiki_file_name = full_url.split("/")[-2]
                    # Edit all links that point to "wiki/File:..."
                    for a_tag in soup.find_all("a", href=True):
                        if f"wiki/Fichier:{wiki_file_name}" in a_tag["href"]:
                            a_tag["href"] = f"../assets/images/{title}_{nbr_img_file}.{img_ext}"


    # Rewrite the HTML page with the new image sources
    with open(f"src/page/{title}.html", "w+", encoding="utf-8") as f:
        f.write(str(soup))
    return page_text

def get_single_page(title, base_url, url):
    global headers

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        page_text = response.text

        # Clean response
        page_text = part_clean(page_text)
        with open(f"src/page/{title}.html", "w+", encoding="utf-8") as f:
            f.write(page_text)

        page_text = download_style(page_text, title, base_url)

        page_text = download_images(page_text, title, base_url)

        print("Extract complete.")

    else:
        print(f"Error {response.status_code}")

#Create folders if no exists
os.makedirs(f"src", exist_ok=True)
os.makedirs(f"src/assets/images", exist_ok=True)
os.makedirs(f"src/assets/videos", exist_ok=True)
os.makedirs(f"src/css", exist_ok=True)
os.makedirs(f"src/page", exist_ok=True)

# Wikipedia page do downloads
title = "Python_(langage)"
base_url = "https://fr.wikipedia.org"
url = f"{base_url}/wiki/{title}"
headers = {"User-Agent": "Mozilla/5.0"}
class_list_to_delete = ["vector-header-container", "vector-sitenotice-container", 
"vector-column-start", "vector-page-toolbar", "bandeau-article", "mw-editsection", "bandeau-section", "navigation-only"]
id_list_to_delete = ["footer-info-copyright", "footer-icons", "footer-places", "p-lang-btn"]

get_single_page(title, base_url, url)