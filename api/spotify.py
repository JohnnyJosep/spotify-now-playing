import os
import json
import random
import requests

from base64 import b64encode
from dotenv import load_dotenv, find_dotenv
from flask import Flask, Response, jsonify, render_template

load_dotenv(find_dotenv())

# Spotify scopes:
#   user-read-currently-playing
#   user-read-recently-played
SPOTIFY_CLIENT_ID = "848547ee07a74436aefeb3cbca4c9296"
SPOTIFY_SECRET_ID = "50b33d195a324ef9b2fb03faf69e6aba"
SPOTIFY_REFRESH_TOKEN = "AQDCGtOwE06L0t9KQaBZ7Ksw-zxhw1N8f0YaTpHnnJKQ9_310zn69GDi_dXQOg7hJUac7vwH3fDauCt-IRvGSNz01VD9zjhj55ym06iol4ybi5HWzt3sbng7hh98vjJgpLc"

REFRESH_TOKEN_URL = "https://accounts.spotify.com/api/token"
NOW_PLAYING_URL = "https://api.spotify.com/v1/me/player/currently-playing"
RECENTLY_PLAYING_URL = (
    "https://api.spotify.com/v1/me/player/recently-played?limit=10"
)

app = Flask(__name__)

def getAuth():
    return b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_SECRET_ID}".encode()).decode(
        "ascii"
    )


def refreshToken():
    data = {
        "grant_type": "refresh_token",
        "refresh_token": SPOTIFY_REFRESH_TOKEN,
    }

    headers = {"Authorization": "Basic {}".format(getAuth())}
    response = requests.post(REFRESH_TOKEN_URL, data=data, headers=headers)

    try:
        return response.json()["access_token"]
    except KeyError:
        print(json.dumps(response.json()))
        print("\n---\n")
        raise KeyError(str(response.json()))


def recentlyPlayed():
    token = refreshToken()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(RECENTLY_PLAYING_URL, headers=headers)

    if response.status_code == 204:
        return {}
    return response.json()


def nowPlaying():
    token = refreshToken()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(NOW_PLAYING_URL, headers=headers)

    if response.status_code == 204:
        return {}
    return response.json()


def loadImageB64(url):
    resposne = requests.get(url)
    return b64encode(resposne.content).decode("ascii")


def makeSVG(data):
    if data == {} or data["item"] == None:
        currentStatus = ""
        recentPlays = recentlyPlayed()
        recentPlaysLength = len(recentPlays["items"])
        itemIndex = random.randint(0, recentPlaysLength - 1)
        item = recentPlays["items"][itemIndex]["track"]
    else:
        item = data["item"]
        currentStatus = "spin"

    image = loadImageB64(item["album"]["images"][1]["url"])
    artistName = item["artists"][0]["name"].replace("&", "&amp;")
    songName = item["name"].replace("&", "&amp;")
    dataDict = {
        "artistName": artistName,
        "songName": songName,
        "image": image,
        "status": currentStatus,
    }

    return render_template("spotify.html.j2", **dataDict)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):
    data = nowPlaying()
    svg = makeSVG(data)

    resp = Response(svg, mimetype="image/svg+xml")
    resp.headers["Cache-Control"] = "s-maxage=1"

    return resp


if __name__ == "__main__":
    app.run(debug=True)
