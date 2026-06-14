import asyncio, edge_tts, groq, random, os, json
from pydub import AudioSegment
from datetime import datetime

VOICES = {
    "GRADY":      {"voice": "en-US-GuyNeural",        "pitch": "-15Hz", "rate": "-20%"},
    "DIAMOND":    {"voice": "en-US-AriaNeural",        "pitch": "+5Hz",  "rate": "+15%"},
    "LOCO":       {"voice": "en-US-TonyNeural",        "pitch": "0Hz",   "rate": "+25%"},
    "PEACHES":    {"voice": "en-US-AmberNeural",       "pitch": "+8Hz",  "rate": "-5%"},
    "STACKS":     {"voice": "en-US-DavisNeural",       "pitch": "-8Hz",  "rate": "-10%"},
    "RED":        {"voice": "en-US-ChristopherNeural", "pitch": "-12Hz", "rate": "-18%"},
    "CHINA DOLL": {"voice": "en-US-JennyNeural",       "pitch": "+3Hz",  "rate": "+5%"},
    "BUBBA":      {"voice": "en-US-TonyNeural",        "pitch": "+2Hz",  "rate": "+20%"},
    "NOVA":       {"voice": "en-US-JennyNeural",       "pitch": "+3Hz",  "rate": "+8%"},
    "GHOST":      {"voice": "en-US-AndrewNeural",      "pitch": "-5Hz",  "rate": "-15%"},
    "TOYA":       {"voice": "en-US-MonicaNeural",      "pitch": "+6Hz",  "rate": "+8%"},
    "KING":       {"voice": "en-US-BrianNeural",       "pitch": "-10Hz", "rate": "-12%"},
}

TOPICS = [
    "Loyalty in the Streets — Is It Dead?",
    "Getting Money Legal vs The Game",
    "Women Holding Down the Hood",
    "Gentrification Taking Over Our Blocks",
    "Street Codes Nobody Follows Anymore",
    "Relationships in the Trap Era",
    "From the Block to the Boardroom",
    "When Your Homie Falls Off",
    "Hood Entrepreneurship — Real Stories",
    "Fake Love vs Real Ones",
    "Raising Kids in the Hood",
    "Social Media and Street Rep",
    "Police, Power, and the People",
    "When the Streets Call You Back",
    "Making It Out Without Forgetting Home"
]

GUESTS = ["LOCO","PEACHES","STACKS","RED","CHINA DOLL",
          "BUBBA","NOVA","GHOST","TOYA","KING"]

GUEST_BIOS = {
    "LOCO":       "East Oakland. Hyphy energy. Talks fast, laughs loud.",
    "PEACHES":    "Memphis. Southern trap queen. Sweet voice, savage mind.",
    "STACKS":     "Chicago Southside. Quiet but deadly with words. Bag man.",
    "RED":        "Houston 3rd Ward. Slow talk. Legacy and generational wealth.",
    "CHINA DOLL": "Compton. Ride or die. Street codes and respect.",
    "BUBBA":      "Miami Overtown. Hype man. Funny, loud, half-true stories.",
    "NOVA":       "Detroit. Militant queen. Pan-African trap wisdom.",
    "GHOST":      "Harlem. Soft-spoken. Spiritual side of street life.",
    "TOYA":       "New Orleans 9th Ward. Voodoo queen. Most quotable.",
    "KING":       "Philadelphia. Old head. Knows every hood's history."
}

def generate_script(topic, today_guests):
    client = groq.Groq(api_key=os.environ["GROQ_API_KEY"])
    guest_context = "\n".join([f"- {g}: {GUEST_BIOS[g]}" for g in today_guests])
    prompt = f"""Write a full 10-minute podcast script for STREET VOICES.
Topic: {topic}
Guests this episode: {', '.join(today_guests)}

HOSTS:
- GRADY: South Central LA. Suga Free x Barry White. Slow, smooth, deep, wise.
  Signature phrases: "You feel me doe", "Let me break it down", "On everything I love"
- DIAMOND: Bronx/ATL. Cardi B x Oprah. Loud, empowering, unbothered.
  Signature phrases: "Periodt.", "Baby let me tell you something", "I said what I said"

GUEST CHARACTERS THIS EPISODE:
{guest_context}

SCRIPT STRUCTURE:
[INTRO - 1 min] Grady opens smooth. Diamond hypes. Introduce topic and guests.
[STREET REPORT - 2 min] All 5 discuss the topic from their hood perspective.
[HOT TAKE - 2 min] Heated debate. Everyone disagrees. Gets real.
[REAL TALK CORNER - 2 min] One character tells a deep personal street story.
[GRIND REPORT - 1.5 min] Hustle, money moves, survival, hood economics.
[OUTRO - 1.5 min] Grady drops wisdom. Diamond closes loud and proud.

FORMAT every single line as: CHARACTER NAME: dialogue
No stage directions. No asterisks. Dialogue only.
Write approximately 3500 words. Raw, authentic street vernacular."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4000
    )
    return response.choices[0].message.content

def parse_script(script_text):
    lines = []
    for line in script_text.strip().split("\n"):
        if ":" in line:
            parts = line.split(":", 1)
            character = parts[0].strip().upper()
            dialogue = parts[1].strip()
            if character in VOICES and dialogue:
                lines.append({"character": character, "text": dialogue})
    return lines

async def speak_line(character, text, output_file):
    """Generate speech audio with retry logic for edge-tts reliability."""
    v = VOICES[character]
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            communicate = edge_tts.Communicate(
                text=text,
                voice=v["voice"],
                pitch=v["pitch"],
                rate=v["rate"]
            )
            await communicate.save(output_file)
            return  # Success
        except Exception as e:
            retry_count += 1
            if retry_count < max_retries:
                print(f"⚠️ TTS retry {retry_count}/{max_retries} for {character}...")
                await asyncio.sleep(2)  # Wait before retry
            else:
                raise Exception(f"TTS failed for {character} after {max_retries} retries: {str(e)}")

async def generate_all_voices(lines, episode_num):
    os.makedirs(f"./episodes/ep{episode_num}/segments", exist_ok=True)
    tasks = []
    for i, line in enumerate(lines):
        out = f"./episodes/ep{episode_num}/segments/{i:04d}_{line['character']}.mp3"
        line["audio_file"] = out
        tasks.append(speak_line(line["character"], line["text"], out))
    await asyncio.gather(*tasks)
    print(f"✅ Generated {len(lines)} voice lines")

def mix_episode(lines, episode_num, topic):
    combined = AudioSegment.empty()
    for line in lines:
        if os.path.exists(line["audio_file"]):
            seg = AudioSegment.from_mp3(line["audio_file"])
            combined += seg + AudioSegment.silent(duration=300)

    safe_topic = topic.replace(" ","_").replace("—","").replace("/","")[:40]
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"StreetVoices_EP{episode_num:03d}_{date_str}_{safe_topic}.mp3"
    out_path = f"./episodes/{filename}"
    combined.export(out_path, format="mp3", bitrate="192k")
    print(f"✅ Episode ready: {filename}")
    return out_path, filename

def save_metadata(episode_num, topic, guests, filename):
    meta = {
        "episode":  episode_num,
        "title":    f"EP{episode_num:03d}: {topic}",
        "topic":    topic,
        "guests":   guests,
        "hosts":    ["GRADY", "DIAMOND"],
        "filename": filename,
        "date":     datetime.now().isoformat(),
        "status":   "ready_to_upload"
    }
    os.makedirs("./episodes", exist_ok=True)
    with open(f"./episodes/ep{episode_num:03d}_meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    print(f"✅ Metadata saved")
    return meta

async def run_episode(episode_number=1):
    print("\n🎙️ STREET VOICES — Generating Episode...\n")
    topic = random.choice(TOPICS)
    today_guests = random.sample(GUESTS, 3)

    print(f"📌 Topic: {topic}")
    print(f"👥 Guests: {', '.join(today_guests)}\n")

    print("🤖 Writing script with Llama 3...")
    script = generate_script(topic, today_guests)
    lines = parse_script(script)
    print(f"📝 Script parsed: {len(lines)} lines\n")

    print("🎙️ Generating voices with Edge-TTS...")
    await generate_all_voices(lines, episode_number)

    print("🎵 Mixing audio...")
    out_path, filename = mix_episode(lines, episode_number, topic)

    meta = save_metadata(episode_number, topic, today_guests, filename)

    print(f"\n✅ DONE! Episode saved to: {out_path}")
    return meta

if __name__ == "__main__":
    import sys
    ep_num = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    asyncio.run(run_episode(episode_number=ep_num))
