<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wikipedia Scrapper</title>
    <style>
        body {
            background-color: #121212;
            color: #e0e0e0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 2rem;
        }

        h1, h2 {
            color: #90caf9;
        }

        ul {
            list-style-type: none;
            padding: 0;
        }

        li {
            margin: 0.5rem 0;
            padding: 0.5rem;
            background-color: #1e1e1e;
            border-radius: 8px;
            transition: background-color 0.3s;
        }

        li:hover {
            background-color: #333;
        }

        a {
            color:rgb(237, 45, 45);
            text-decoration: none;
            font-weight: bold;
        }

        a:hover {
            text-decoration: underline;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
        }

        .error {
            color: #f44336;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Wikipedia Scrapper</h1>
        <h2>Articles</h2>
        <ul>
        <?php
        try {
            // Connexion to database with PDO
            $pdo = new PDO(
                'mysql:host=mysql;port=3306;dbname=wikipedia;charset=utf8mb4',
                'user',
                'userpassword',
                [
                    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                ]
            );

            // request get all url already scrap
            $req = $pdo->prepare("SELECT title, url FROM url_aldrealy_scrap");
            $success = $req->execute();

            if ($success && $req->rowCount() > 0) {
                foreach ($req as $row) {
                    // Split l'url 
                    $spl = explode("https://fr.wikipedia.org/wiki/", $row["url"]);
                    $url = $spl[1];
                    echo "<li><a href='page/" . $url . ".html' target='_blank'>" . htmlspecialchars($row["title"]) . "</a></li>";
                }
            } else {
                echo "<li>Empty.</li>";
            }

        } catch (PDOException $e) {
            echo "<p class='error'>Database error: " . htmlspecialchars($e->getMessage()) . "</p>";
        }
        ?>
        </ul>
    </div>
</body>
</html>
