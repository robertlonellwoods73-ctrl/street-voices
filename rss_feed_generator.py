import json, os, glob
from datetime import datetime, timezone
from email.utils import formatdate
from mutagen.mp3 import MP3
import xml.etree.ElementTree as ET
from flask import Flask, send_file, jsonify

PODCAST_CONFIG = {
    "title":           "Street Voices",
    "description":     "Real Talk. Hood Wisdom. No Filter. Grady, Diamond, and rotating hood legends break down street life, the grind, hustle culture, and everything in between. New episode every 12 hours.",
    "author":          "Street Voices Podcast",
    "email":           "streetvoicespod@gmail.com",
    "website":         "https://your-username.github.io/street-voices",
    "language":        "en-us",
    "category":        "Society &amp; Culture",
    "explicit":        "yes",
    "image_url":       "https://your-username.github.io/street-voices/cover.jpg",
    "episodes_folder": "./episodes",
    "base_audio_url":  "https://your-username.github.io/street-voices/episodes",
    "rss_output_file": "./feed.xml",
}

def load_all_episodes():
    episodes = []
    meta_files = glob.glob(f"{PODCAST_CONFIG['episodes_folder']}/ep*_meta.json")
    meta_files.sort(reverse=True)

    for meta_file in meta_files:
        with open(meta_file) as f:
            meta = json.load(f)

        mp3_path = f"{PODCAST_CONFIG['episodes_folder']}/{meta['filename']}"
        duration_secs = 600
        file_size = 0

        if os.path.exists(mp3_path):
            try:
                audio = MP3(mp3_path)
                duration_secs = int(audio.info.length)
                file_size = os.path.getsize(mp3_path)
            except:
                pass

        episodes.append({
            "number":      meta["episode"],
            "title":       meta["title"],
            "topic":       meta["topic"],
            "guests":      meta["guests"],
            "filename":    meta["filename"],
            "date":        meta["date"],
            "duration":    format_duration(duration_secs),
            "file_size":   file_size,
            "audio_url":   f"{PODCAST_CONFIG['base_audio_url']}/{meta['filename']}",
            "description": build_description(meta),
        })
    return episodes

def format_duration(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"

def format_rss_date(iso_date_str):
    try:
        dt = datetime.fromisoformat(iso_date_str)
        dt = dt.replace(tzinfo=timezone.utc)
        return formatdate(dt.timestamp(), usegmt=True)
    except:
        return formatdate(usegmt=True)

def build_description(meta):
    guests_str = ", ".join(meta.get("guests", []))
    return (
        f"Episode {meta['episode']:03d}: {meta['topic']}\n\n"
        f"Grady and Diamond are back with {guests_str} to break down: {meta['topic']}.\n\n"
        f"Real talk from real hoods. No filter, no fluff.\n\n"
        f"Featuring: GRADY · DIAMOND · {guests_str}\n\n"
        f"#StreetVoices #HoodPodcast #RealTalk #Hustle"
    )

def build_rss_feed(episodes):
    cfg = PODCAST_CONFIG
    rss = ET.Element("rss", {
        "version": "2.0",
        "xmlns:itunes":   "http://www.itunes.com/dtds/podcast-1.0.dtd",
        "xmlns:content":  "http://purl.org/rss/1.0/modules/content/",
        "xmlns:atom":     "http://www.w3.org/2005/Atom",
    })
    channel = ET.SubElement(rss, "channel")

    def tag(parent, name, text=None, **attrs):
        el = ET.SubElement(parent, name, attrs)
        if text: el.text = text
        return el

    tag(channel, "title",         cfg["title"])
    tag(channel, "link",          cfg["website"])
    tag(channel, "language",      cfg["language"])
    tag(channel, "description",   cfg["description"])
    tag(channel, "lastBuildDate", formatdate(usegmt=True))

    tag(channel, "atom:link",
        href=f"{cfg['website']}/feed.xml",
        rel="self",
        type="application/rss+xml")

    tag(channel, "itunes:author",   cfg["author"])
    tag(channel, "itunes:summary",  cfg["description"])
    tag(channel, "itunes:explicit", cfg["explicit"])
    tag(channel, "itunes:type",     "episodic")

    owner = ET.SubElement(channel, "itunes:owner")
    tag(owner, "itunes:name",  cfg["author"])
    tag(owner, "itunes:email", cfg["email"])

    cat = ET.SubElement(channel, "itunes:category", text=cfg["category"])
    ET.SubElement(channel, "itunes:image", href=cfg["image_url"])

    for ep in episodes:
        item = ET.SubElement(channel, "item")
        tag(item, "title",       ep["title"])
        tag(item, "description", ep["description"])
        tag(item, "pubDate",     format_rss_date(ep["date"]))
        tag(item, "guid",        f"{cfg['website']}/ep/{ep['number']}", isPermaLink="true")

        ET.SubElement(item, "enclosure", {
            "url":    ep["audio_url"],
            "length": str(ep["file_size"]),
            "type":   "audio/mpeg"
        })

        tag(item, "itunes:title",       ep["title"])
        tag(item, "itunes:summary",     ep["description"])
        tag(item, "itunes:duration",    ep["duration"])
        tag(item, "itunes:explicit",    "yes")
        tag(item, "itunes:episode",     str(ep["number"]))
        tag(item, "itunes:episodeType", "full")

    return rss

def save_feed(rss_element):
    tree = ET.ElementTree(rss_element)
    ET.indent(tree, space="  ")
    output = PODCAST_CONFIG["rss_output_file"]
    tree.write(output, encoding="UTF-8", xml_declaration=True)
    count = len(rss_element.find("channel").findall("item"))
    print(f"✅ RSS feed saved: {output} ({count} episodes)")

def add_episode_to_feed(meta):
    episodes = load_all_episodes()
    rss_el = build_rss_feed(episodes)
    save_feed(rss_el)
    print(f"📡 Feed updated — Spotify/Apple will pick this up within 1 hour")

def serve_feed():
    app = Flask(__name__)

    @app.route("/feed.xml")
    def rss():
        episodes = load_all_episodes()
        rss_el = build_rss_feed(episodes)
        save_feed(rss_el)
        return send_file(PODCAST_CONFIG["rss_output_file"],
                         mimetype="application/rss+xml")

    @app.route("/episodes")
    def episode_list():
        return jsonify(load_all_episodes())

    @app.route("/health")
    def health():
        eps = load_all_episodes()
        return jsonify({
            "status":   "live",
            "show":     "Street Voices",
            "episodes": len(eps),
            "latest":   eps[0]["title"] if eps else "No episodes yet"
        })

    print("\n🎙️ Street Voices RSS Server Running!")
    print(f"   Feed: http://localhost:5000/feed.xml")
    app.run(host="0.0.0.0", port=5000, debug=False)

def print_submission_guide():
    feed_url = f"{PODCAST_CONFIG['website']}/feed.xml"
    print(f"""
╔══════════════════════════════════════════════════╗
║   STREET VOICES — Platform Submission Guide      ║
╠══════════════════════════════════════════════════╣
║ Your RSS Feed URL:                               ║
║ {feed_url:<48} ║
╠══════════════════════════════════════════════════╣
║  SPOTIFY  → podcasters.spotify.com              ║
║  APPLE    → podcastsconnect.apple.com           ║
║  AMAZON   → music.amazon.com/podcasts/submit    ║
║  GOOGLE   → podcastsmanager.google.com          ║
║  IHEART   → iheart.com/podcast/submit           ║
╚══════════════════════════════════════════════════╝
    """)

if __name__ == "__main__":
    impor
