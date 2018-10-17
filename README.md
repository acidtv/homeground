# Homeground

Homeground is a site to help you find a suitable area to live. By selecting the things
you find important to have nearby it shows you the parts of town that meet these requirements,
so you know where to look for a new home.

![Homeground preview](/images/preview.png)

## Running

It's easiest to run Homeground with docker compose. A compose file is included. Just clone
the repo and run `$ docker-compose up`.

After starting the application for the first time initialize the data by downloading an 
openstreetmap export file to the app folder and execute:

```
$ docker-compose exec app /bin/bash
$ flask import-osm <openstreetmap-export.xml>
```

You can now load up your browser and head to http://localhost:5000/.
