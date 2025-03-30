import requests
from bs4 import BeautifulSoup, Comment
from urllib.parse import urljoin, unquote
import cssutils
import logging
import os
import mysql.connector

# Desactivate warnings of cssutils
cssutils.log.setLevel(logging.CRITICAL)

# Wikipedia page do downloads
# title = "Python_(langage)"
base_url = "https://fr.wikipedia.org"
headers = {"User-Agent": "Mozilla/5.0"}
class_list_to_delete = ["vector-header-container", "vector-sitenotice-container", 
"vector-column-start", "vector-page-toolbar", "bandeau-article", "mw-editsection", "bandeau-section", "navigation-only"]
id_list_to_delete = ["footer-info-copyright", "footer-icons", "footer-places", "p-lang-btn"]


mydb = mysql.connector.connect(
  host="localhost",
  user="user",
  password="userpassword",
  database="wikipedia",
  charset="utf8mb4"
)

# Check if table exist
mycursor = mydb.cursor(buffered=True)
mycursor.execute("SHOW TABLES LIKE 'url_to_scrap'")
result1 = mycursor.fetchone()

mycursor.execute("SHOW TABLES LIKE 'url_aldrealy_scrap'")
result2 = mycursor.fetchone()
if not result1:
    # create table link_to_scrap with id, title, url
    mycursor.execute("""
    CREATE TABLE url_to_scrap (
        id INT AUTO_INCREMENT PRIMARY KEY, 
        title VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci, 
        url VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """)
    # Insert a link to scrap
    mycursor.execute("INSERT INTO url_to_scrap (title, url) VALUES ('Python_(langage)', 'https://fr.wikipedia.org/wiki/Python_(langage)')")

if not result2:
    mycursor.execute("""
    CREATE TABLE url_aldrealy_scrap (
        id INT AUTO_INCREMENT PRIMARY KEY, 
        title VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci, 
        url VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """)
    
    mydb.commit()



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
    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(page_text, "html.parser")

    # Find all images in <a> tags
    nbr_img_file = 0  # Counter for files
    image_links_map = {}  # Dictionary to store correspondences { filename : localpath }

    for a_tag in soup.find_all("a", href=True):
        img = a_tag.find("img")  # Checks if the <a> contains an image
        if img:
            src = img.get("src")
            if src:
                # Incrementing the counter
                nbr_img_file += 1
                full_url = urljoin(base_url, src)  # Absolute URL of the image
                img_ext = os.path.splitext(full_url)[-1]  # Image extension

                # Extract file name from image
                img_filename = unquote(full_url.split("/")[-1])  # Decode the %20

                img_path = f"src/assets/images/{title}_{nbr_img_file}{img_ext}"
                img_path_href = f"../assets/images/{title}_{nbr_img_file}{img_ext}"

                # Download the image if it doesn't exist yet
                if (full_url != "https://login.wikimedia.org/wiki/Special:CentralAutoLogin/start?useformat=desktop&type=1x1&usesul3=0"
                        and not os.path.exists(img_path)):
                    response_img = requests.get(full_url, headers=headers)
                    if response_img.status_code == 200:
                        with open(img_path, "wb+") as f:
                            f.write(response_img.content)

                # Change the image to point to the local file
                img["src"] = img_path_href
                img["srcset"] = img_path_href

                # Associate the file with the correct local path
                image_links_map[img_filename] = img_path_href

                # Change the `href` attribute of the <a> to point to the local image
                a_tag["href"] = img_path_href

    # Rewrite the HTML file with the changes
    with open(f"src/page/{title}.html", "w+", encoding="utf-8") as f:
        f.write(str(soup))

    return str(soup)

def download_videos(page_text, title, base_url):
    global headers
    soup = BeautifulSoup(page_text, "html.parser")
    videos = soup.find_all("video")

    os.makedirs("src/assets/videos", exist_ok=True)  # Create the folder if it does not exist

    nbr_video_file = 0  # Video counter

    for video in videos:
        src = video.get("src")
        
        if not src:
            # Check if the video has sources `<source src="...">`
            source_tag = video.find("source")
            if source_tag:
                src = source_tag.get("src")

        if src:
            nbr_video_file += 1  # Increment the counter
            full_url = urljoin(base_url, src)  # Convert to absolute URL
            video_ext = full_url.split(".")[-1].split("?")[0]  # Extract clean extension
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
            if video.get("poster"):
                video["poster"] = "../static/poster-video.png"
            
            # Update all sources `<source>` of the video
            for source in video.find_all("source"):
                source["src"] = f"../assets/videos/{title}_{nbr_video_file}.{video_ext}"

    # Rewrite the HTML page with the new video sources
    with open(f"src/page/{title}.html", "w+", encoding="utf-8") as f:
        f.write(str(soup))

    return str(soup)  # Return the modified version with `soup`

def download_audio(page_text, title, base_url):
    global headers
    soup = BeautifulSoup(page_text, "html.parser")
    audios = soup.find_all("audio")

    os.makedirs("src/assets/audio", exist_ok=True)  # Create the folder if it does not exist

    nbr_audio_file = 0  # Audio file counter

    for audio in audios:
        src = audio.get("src")
        
        if not src:
            # Check if the audio has <source> tags
            source_tag = audio.find("source")
            if source_tag:
                src = source_tag.get("src")

        if src:
            nbr_audio_file += 1  # Increment the counter
            full_url = urljoin(base_url, src)  # Convert to absolute URL
            audio_ext = full_url.split(".")[-1].split("?")[0]  # Extract the clean extension
            audio_path = f"src/assets/audio/{title}_{nbr_audio_file}.{audio_ext}"

            if not os.path.exists(audio_path):
                response_audio = requests.get(full_url, headers=headers, stream=True)

                if response_audio.status_code == 200:
                    with open(audio_path, "wb") as f:
                        for chunk in response_audio.iter_content(chunk_size=8192):
                            f.write(chunk)

            # Edit `src` in `soup`
            if audio.get("src"):
                audio["src"] = f"../assets/audio/{title}_{nbr_audio_file}.{audio_ext}"
            
            # Update all `<source>` of the audio
            for source in audio.find_all("source"):
                source["src"] = f"../assets/audio/{title}_{nbr_audio_file}.{audio_ext}"

    # Rewrite the HTML page with the new audio file paths
    with open(f"src/page/{title}.html", "w+", encoding="utf-8") as f:
        f.write(str(soup))

    return str(soup)  # Returns the modified version with `soup`

def insert_wiki_link(page_text, title, base_url):
    # Analyse du HTML avec BeautifulSoup
    soup = BeautifulSoup(page_text, "html.parser")

    # Retrieve all links with a title attribute
    links = soup.find_all("a", title=True)

    for link in links:
        original_href = link.get("href")
        title_href = link.get("title")

        if original_href and title_href:
            # Transform url
            if original_href.startswith("/wiki/") and ":" not in original_href:
                slug_page = unquote(original_href.split("/")[-1])  # Retrieve the page slug
                new_url = f"http://wiki.ixem/page/{slug_page}.html"
                old_url = f"{base_url}/wiki/{slug_page}"

                # Check if the URL already exists in url_to_scrap
                mycursor.execute("SELECT * FROM url_to_scrap WHERE url = %s", (old_url,))
                result_request1 = mycursor.fetchone()
                if not result_request1:
                     # Check if the URL already exists in url_aldrealy_scrap
                        mycursor.execute("SELECT * FROM url_aldrealy_scrap WHERE url = %s", (old_url,))
                        result_request2 = mycursor.fetchone()
                        if not result_request2:
                            # Insertion into database
                            sql = "INSERT INTO url_to_scrap (title, url) VALUES (%s, %s)"
                            values = (title_href, old_url)
                            mycursor.execute(sql, values)
                            mydb.commit()


                # change the href of the link
                link["href"] = new_url

    
    # Rewrite the HTML page with the new audio file paths
    with open(f"src/page/{title}.html", "w+", encoding="utf-8") as f:
        f.write(str(soup))

    return str(soup)  # Returns the modified version with `soup`

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

        resultat_audio = download_audio(resultat_video, title, base_url)

        resultat_add_link = insert_wiki_link(resultat_audio, title, base_url)

    else:
        print(f"Error {response.status_code}")

#Create folders if no exists
os.makedirs(f"src", exist_ok=True)
os.makedirs(f"src/assets/images", exist_ok=True)
os.makedirs(f"src/assets/videos", exist_ok=True)
os.makedirs(f"src/assets/audio", exist_ok=True)
os.makedirs(f"src/css", exist_ok=True)
os.makedirs(f"src/page", exist_ok=True)
os.makedirs(f"src/static", exist_ok=True)

while True:
    mycursor.execute("SELECT * FROM url_to_scrap LIMIT 1")

    # If there are no rows, break the loop
    myresult = mycursor.fetchone()

    if not myresult:
        print("No more pages to download.")
        break

    titleh1 = myresult[1]
    url = myresult[2]
    title = url.split("/")[-1]  # Extract the last part of the URL

    # Call the function to download the page
    get_single_page(title, base_url, url)    # Delete the row from the database
    mycursor.execute(f"DELETE FROM url_to_scrap WHERE id = {myresult[0]}")
    mycursor.execute("INSERT INTO url_aldrealy_scrap (title, url) VALUES (%s, %s)", (titleh1, url))

    mydb.commit()


    

