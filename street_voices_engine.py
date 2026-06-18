async def generate_all_voices(lines, episode_num):
    os.makedirs(f"./episodes/ep{episode_num}/segments", exist_ok=True)
    for i, line in enumerate(lines):
        out = f"./episodes/ep{episode_num}/segments/{i:04d}_{line['character']}.mp3"
        line["audio_file"] = out
        success = False
        for attempt in range(5):
            try:
                await speak_line(line["character"], line["text"], out)
                await asyncio.sleep(0.5)
                success = True
                break
            except Exception as e:
                wait = (attempt + 1) * 3
                print(f"⚠️ Retry {attempt+1}/5 for {line['character']} (waiting {wait}s)...")
                await asyncio.sleep(wait)
        if not success:
            print(f"⚠️ Skipping {line['character']} line {i} after 5 attempts")
        if i % 10 == 0:
            print(f"🎙️ Progress: {i}/{len(lines)} lines done...")
    print(f"✅ Generated {len(lines)} voice lines")
