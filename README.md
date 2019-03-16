Stalky
============
![](https://img.shields.io/badge/license-MIT-green.svg)
![](https://img.shields.io/github/languages/code-size/JakuJ/zzzzz.svg)
![](https://img.shields.io/github/last-commit/JakuJ/zzzzz.svg)
![](https://img.shields.io/badge/creepiness-passable-orange.svg)

What is this?
-------------
A complete remake of a project by [Alexander Hogue](https://github.com/defaultnamehere/zzzzz).
Read [his blog post](https://mango.pdf.zone/graphing-when-your-facebook-friends-are-awake) to get an idea of what this is or watch [his talk](https://www.youtube.com/watch?v=MkSkqMvGBuo) at PyCon Australia 2016.

Why is this?
------------

As a student with the circadian rhythm probably completely out of tune, I thought it wuld be a fun eperiment to check whether other students struggle to go to sleep at reasonable times as well.

Researching the topic of sleep pattern analysis I stumbled upon [this repository](https://github.com/defaultnamehere/zzzzz), which collects data from Facebook's internal API,  but Facebook changed the API long ago and the program didn't work, so I decided to use the repo as a starting point in making a new tool.

Installation
-----------

Run 
```bash
make install
```

You'll also need to supply some way of authenticating yourself to Facebook.
Do this by creating a SECRETS.json file with the following fields:

```json
{
    "uid": "<Your Facebook user id>",
    "cookie": "<Your Facebook cookie>",
    "client_id": "<Your Facebook client id>"
}
```

You can find your FB client ID by inspecting the GET parameters sent when your browser requests `facebook.com/pull` using your browser's dev tools.

Gathering data
--------------

```bash
make fetcher
```

This will run the fetcher script indefinitely (restarting on crashes), creating data in "data" folder. You can for example host this on a microcomputer (e.g., Raspberry Pi) running 24/7.
Depending on the number of Facebook friends you have, and how active they are, you can expect around 20 - 40 MB per day to be written to disk.

Plotting some graphs
----------------
### Displaying singular user's activity

1. Run `make server` to start the visualization webapp
2. Go to <http://localhost:5001> to view it
3. Search by FB User Name a user whose activity you want to graph into the box.

The "webapp" uses basic authentication that can be enabled by creating an `auth_hash.txt` file which contains a MD5 hash of a concatenation of valid username and password pair.

### Analysing the data

1. Open the *analysis.ipynb* Jupyter notebook
1. Run first few cells to load all data from the *data* folder
2. The following cells create an interpolated timeseries and do stuff with it, like displaying a chart of average actiity of all users (or a specific user) throughout the day, visualizing similarities between sleep patterns (2-dimensional PCA chart) and other stuff.