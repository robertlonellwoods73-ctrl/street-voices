import asyncio, sys, os, glob

async def run_autopilot():

    print("""
╔══════════════════════════════════════════╗
║   🎙️  STREET VOICES AUTOPILOT v2.0      ║
║   Real Talk. Hood Wisdom. No Filter.    ║
╚══════════════════════════════════════════╝
    """)

    # Auto-detect episode number
    existing = glob.glob("./episodes/ep*_meta.json")
    episode_number = len(existing) + 1
    print(f"📌 Generating Episode {episode_number:03d}...\n")

    # Step 1: Generate script and voices
    print("━━━ STEP 1/3: Script + Voices ━━━━━━━━━━")
    from street_voices_engine import run_episode
    meta = await run_episode(episode_number=episode_number)

    # Step 2: Update RSS feed
    print("\n━━━ STEP 2/3: Update RSS Feed ━━━━━━━━━━")
    from rss_feed_generator import add_episode_to_feed
    add_episode_to_feed(meta)

    # Step 3: Create export package
    print("\n━━━ STEP 3/3: Export Package ━━━━━━━━━━━")
    export_dir = f"./export/StreetVoices_EP{episode_number:03d}"
    os.makedirs(export_dir, exist_ok=True)

    audio_path = f"./episodes/{meta['filename']}"

    # Write upload-ready caption
    guests_str = ", ".join(meta["guests"])
    caption = f"""🎙️ STREET VOICES EP{episode_number:03d}
"{meta['topic']}"
Feat. {guests_str}

Real Talk. Hood Wisdom. No Filter. 🔥

#StreetVoices #HoodPodcast #RealTalk #StreetLife
#Hustle #Grind #PodcastLife #BlackPodcast"""

    with open(f"{export_dir}/caption.txt", "w") as f:
        f.write(caption)

    with open(f"{export_dir}/upload_checklist.txt", "w") as f:
        f.write(f"""STREET VOICES EP{episode_number:03d} — UPLOAD CHECKLIST
Topic: {meta['topic']}
Guests: {guests_str}
File: {meta['filename']}

[ ] Spotify      — auto via RSS feed (done automatically)
[ ] Apple        — auto via RSS feed (done automatically)
[ ] TikTok       — upload MP3, paste caption.txt
[ ] YouTube      — upload as audio podcast video
[ ] Instagram    — upload as Reel, paste caption.txt
""")

    print(f"✅ Export package ready: {export_dir}")

    # Done
    print(f"""
╔══════════════════════════════════════════╗
║  ✅ EPISODE {episode_number:03d} COMPLETE!              ║
╠══════════════════════════════════════════╣
║  Topic:  {meta['topic'][:38]:<38} ║
║  Guests: {guests_str[:38]:<38} ║
╠══════════════════════════════════════════╣
║  Spotify + Apple get this automatically ║
║  Check ./export/ for TikTok/Instagram   ║
╚══════════════════════════════════════════╝
    """)

    return meta

if __name__ == "__main__":
    asyncio.run(run_autopilot())
