Stalky
============

![](https://img.shields.io/badge/creepiness-medium-orange.svg)

What is this?
-------------
A complete remake of a (long forgotten ?) project by [Alexander Hogue](https://github.com/defaultnamehere/zzzzz).
Read [his blog post](https://mango.pdf.zone/graphing-when-your-facebook-friends-are-awake) to get an idea of what this is.

Why is this?
------------

As a student with the circadian rhythm probably completely out of tune, I got inspired to check whether my other student friends go to sleep at reasonable times.

Looking for an idea I stumbled upon [this repository](https://github.com/defaultnamehere/zzzzz), but Facebook changed the API long ago, so I decided to use it as a starting point in making a new tool.

 There is probably a correlation between having good sleep habits and getting good grades, so who knows what data science can be applied to such data?

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
    "uid": "Your Facebook user id",
    "cookie": "Your Facebook cookie",
    "client_id": "Your Facebook client id"
}
```

You can find your FB client ID by inspecting the GET parameters sent when your browser requests `facebook.com/pull` using your browser's dev tools.

Gathering data
--------------

```bash
make fetcher
```

This will run the fetcher script indefinitely (restarting on crashes), creating data in "log". You can for example host this on a microcomputer running 24/7.
Depending on the number of Facebook friends you have, and how active they are, you can expect around 20 - 40 MB per day to be written to disk.

Make some graphs
----------------

1. Run `make server` to start the 100% CSS-free "webapp"
2. Go to <http://localhost:5001> to view the ultra-minimal "webapp"
3. Search by FB User Name a user whose activity you want to graph into the box.