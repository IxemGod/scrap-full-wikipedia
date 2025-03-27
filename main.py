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
            if not os.path.exists(f"src/css/{title}{nbr_style_file}.css"):
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
            img_ext = full_url.split(".")[-1]  # Retrieve the image extension
            # Download the image file
            if(full_url != "https://login.wikimedia.org/wiki/Special:CentralAutoLogin/start?useformat=desktop&type=1x1&usesul3=0" and os.path.exists(f"../assets/images/{title}_{nbr_img_file}.{img_ext}")):
                response_img = requests.get(full_url, headers=headers)
                if response_img.status_code == 200:
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

    return str(soup)

def download_videos(page_text, title, base_url):
    global headers
    soup = BeautifulSoup(page_text, "html.parser")
    videos = soup.find_all("video")

    os.makedirs("src/assets/videos", exist_ok=True)  # Créer le dossier si inexistant

    nbr_video_file = 0  # Compteur de vidéos

    for video in videos:
        src = video.get("src")
        
        if not src:
            # Vérifier si la vidéo a des sources `<source src="...">`
            source_tag = video.find("source")
            if source_tag:
                src = source_tag.get("src")

        if src:
            nbr_video_file += 1  # Incrémenter le compteur
            full_url = urljoin(base_url, src)  # Convertir en URL absolue
            video_ext = full_url.split(".")[-1].split("?")[0]  # Extraire extension propre
            video_path = f"src/assets/videos/{title}_{nbr_video_file}.{video_ext}"

            if not os.path.exists(video_path):
                response_video = requests.get(full_url, headers=headers, stream=True)

                if response_video.status_code == 200:
                    
                    with open(video_path, "wb") as f:
                        for chunk in response_video.iter_content(chunk_size=8192):
                            f.write(chunk)

                    # Modifier `src` dans `soup`
                    if video.get("src"):
                        video["src"] = f"../assets/videos/{title}_{nbr_video_file}.{video_ext}"
                    
                    # Mettre à jour toutes les sources `<source>` de la vidéo
                    for source in video.find_all("source"):
                        source["src"] = f"../assets/videos/{title}_{nbr_video_file}.{video_ext}"

    # Réécrire la page HTML avec les nouvelles sources des vidéos
    with open(f"src/page/{title}.html", "w+", encoding="utf-8") as f:
        f.write(str(soup))

    return str(soup)  # Retourner la version modifiée avec `soup`

def get_single_page(title, base_url, url):
    global headers

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        page_text = response.text

        # Clean response
        page_text = part_clean(page_text)
        with open(f"src/page/{title}.html", "w+", encoding="utf-8") as f:
            f.write(page_text)

        resultat_style = download_style(page_text, title, base_url)

        resultat_images = download_images(resultat_style, title, base_url)

        resultat_video = download_videos(resultat_images, title, base_url)


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
# title = "Python_(langage)"
title = "Apollo_11"
base_url = "https://fr.wikipedia.org"
url = f"{base_url}/wiki/{title}"
headers = {"User-Agent": "Mozilla/5.0"}
class_list_to_delete = ["vector-header-container", "vector-sitenotice-container", 
"vector-column-start", "vector-page-toolbar", "bandeau-article", "mw-editsection", "bandeau-section", "navigation-only"]
id_list_to_delete = ["footer-info-copyright", "footer-icons", "footer-places", "p-lang-btn"]

get_single_page(title, base_url, url)