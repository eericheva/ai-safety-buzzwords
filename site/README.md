# site/

What https://mrswallbreakermaps.com takes from this repository, and nothing else.

`site.json` is the whole contract. `title` and `desc` fill the project card on the site's home
page, `preview` is the card's image, and `files` maps each URL under the project's address on the
site to a file in this repository. The site pins this repository by commit and copies exactly the
listed files at that commit, so a file not listed here never reaches the site.
