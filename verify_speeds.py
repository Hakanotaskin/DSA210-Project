import fastf1

# Enable cache to speed this up if you run it twice
fastf1.Cache.enable_cache('logs/') # Assuming you have a logs/ or cache/ directory

print("--- Verifying Dutch GP 2023 (Ocon) ---")
session_zandvoort = fastf1.get_session(2023, 'Dutch Grand Prix', 'Q')
session_zandvoort.load(telemetry=False, weather=False, messages=False) # Only need laps
laps_zandvoort = session_zandvoort.laps
ocon_laps = laps_zandvoort.pick_driver('OCO')
print(f"Ocon Max Speed (Zandvoort): {ocon_laps['SpeedST'].max()} km/h")

print("\n--- Verifying São Paulo 2024 (Norris & Albon) ---")
session_brazil = fastf1.get_session(2024, 'São Paulo Grand Prix', 'Q')
session_brazil.load(telemetry=False, weather=False, messages=False)
laps_brazil = session_brazil.laps
nor_laps = laps_brazil.pick_driver('NOR')
alb_laps = laps_brazil.pick_driver('ALB')
print(f"Norris Max Speed (Brazil): {nor_laps['SpeedST'].max()} km/h")
print(f"Albon Max Speed (Brazil): {alb_laps['SpeedST'].max()} km/h")
