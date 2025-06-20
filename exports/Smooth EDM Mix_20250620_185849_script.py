#!/usr/bin/env python3
"""
AI Music Mixer - Generated PyDub Script
Mix: Untitled
Generated: 2025-06-20T18:59:23.737354
"""

from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range

# Load audio files
track_0 = AudioSegment.from_file("SondreDrakensson_Do Robots Get Bored_530217.mp3")
track_0 = normalize(track_0)
track_1 = AudioSegment.from_file("Universfield_Ambient Background Music for Peaceful Moments_736265.mp3")
track_1 = normalize(track_1)
track_2 = AudioSegment.from_file("Metrolynn_derpy electronic song_761465.mp3")
track_2 = normalize(track_2)
track_3 = AudioSegment.from_file("AudioCoffee_Abstract Technology loop ver1_736800.mp3")
track_3 = normalize(track_3)
track_4 = AudioSegment.from_file("AudioCoffee_Abstract Technology loop ver2_736801.mp3")
track_4 = normalize(track_4)
track_5 = AudioSegment.from_file("AudioCoffee_Abstract Technology short version_736802.mp3")
track_5 = normalize(track_5)

# Create mix
mixed = track_0.fade_in(3000)
mixed = mixed + track_1.fade_in(1500)
mixed = mixed + track_2.fade_in(1500)
mixed = mixed + track_3.fade_in(1500)
mixed = mixed + track_4.fade_in(1500)
mixed = mixed + track_5.fade_in(1500)

# Final processing
mixed = normalize(mixed)
mixed = compress_dynamic_range(mixed)
mixed.export("final_mix.mp3", format="mp3", bitrate="320k")
