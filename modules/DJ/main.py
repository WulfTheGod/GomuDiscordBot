import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import asyncio
import json
import os
import re
import lyricsgenius

# Global playlist queue for managing songs
playlist_queue = []


class DJ(commands.Cog):
    """DJ functionality for the bot."""

    def __init__(self, bot):
        self.bot = bot
        self.config = self._load_config()
        self.current_song = None
        # Initialize Genius API client
        self.genius = lyricsgenius.Genius(os.getenv('GENIUS_ACCESS_TOKEN'))
        # Turn off status messages from Genius
        self.genius.verbose = False
        print("DJ cog initialized.")

    def _load_config(self):
        """Load config from JSON file."""
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {
                "max_queue_size": 50,
                "auto_disconnect_minutes": 5,
                "allowed_sources": ["youtube"]
            }

    @app_commands.command(name="play", description="Play a song by link or search query")
    async def play(self, interaction: discord.Interaction, query: str):
        """Plays a song from YouTube."""
        await interaction.response.defer()

        # Check if user is in a voice channel
        if not interaction.user.voice:
            await interaction.followup.send(
                f"🎵 {interaction.user.mention}, you need to be in a voice channel!"
            )
            return

        # Get or join voice channel
        if not interaction.guild.voice_client:
            await interaction.user.voice.channel.connect()

        try:
            with yt_dlp.YoutubeDL({"format": "bestaudio", "noplaylist": "True"}) as ydl:
                try:
                    # Try to get video info from URL
                    info = ydl.extract_info(f"ytsearch:{query}", download=False)
                    if "entries" in info:
                        info = info["entries"][0]
                    url = info["webpage_url"]
                except Exception as e:
                    print(f"Error extracting info: {e}")
                    await interaction.followup.send(
                        f"❌ {interaction.user.mention}, I couldn't find that song!"
                    )
                    return

            # Add to queue
            playlist_queue.append(url)

            # If nothing is playing, start playing
            if not interaction.guild.voice_client.is_playing():
                await self.play_next(interaction)
            else:
                await interaction.followup.send(
                    f"🎵 {interaction.user.mention}, added **{info['title']}** to the queue!"
                )

        except Exception as e:
            print(f"Error in play command: {e}")
            await interaction.followup.send(
                f"❌ {interaction.user.mention}, there was an error playing that song!"
            )

    @app_commands.command(name="skip", description="Skip the current track")
    async def skip(self, interaction: discord.Interaction):
        """Skips the current track."""
        if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.stop()
            await interaction.response.send_message(
                f"⏭️ {interaction.user.mention}, I skipped the track! Let's keep sailing! ⛵"
            )
        else:
            await interaction.response.send_message(
                f"🤔 {interaction.user.mention}, there's no track to skip! 🎧"
            )

    @app_commands.command(name="stop", description="Stop playback and disconnect")
    async def stop(self, interaction: discord.Interaction):
        """Stops playback and disconnects the bot."""
        global playlist_queue
        
        try:
            await interaction.response.defer()
            
            if interaction.guild.voice_client:
                # Clear the queue
                playlist_queue = []
                
                # Stop playing if currently playing
                if interaction.guild.voice_client.is_playing():
                    interaction.guild.voice_client.stop()
                
                # Disconnect
                await interaction.guild.voice_client.disconnect()
                
                await interaction.followup.send(
                    f"⚓ {interaction.user.mention}, I stopped the music! 🌊"
                )
            else:
                await interaction.followup.send(
                    f"⚓ {interaction.user.mention}, I'm not even in a voice channel! 🤷"
                )
        except Exception as e:
            print(f"Error in stop command: {e}")
            await interaction.followup.send(
                f"❌ {interaction.user.mention}, there was an error stopping the music!"
            )

    @app_commands.command(name="lyrics", description="Show lyrics for the current song")
    async def lyrics(self, interaction: discord.Interaction):
        """Shows lyrics for the current song."""
        await interaction.response.defer()

        if not self.current_song:
            await interaction.followup.send(
                f"🎵 {interaction.user.mention}, there's no song playing right now!"
            )
            return

        try:
            # Clean up the title for better search results
            search_title = self.current_song['title']
            search_title = re.sub(r'\(.*?\)', '', search_title)
            search_title = re.sub(r'\[.*?\]', '', search_title)
            search_title = re.sub(r'official.*?video', '', search_title, flags=re.IGNORECASE)
            search_title = ' '.join(search_title.split())

            # Search for the song
            song = self.genius.search_song(search_title)
            
            if song and song.lyrics:
                # Clean up lyrics
                lyrics = song.lyrics.split('Lyrics')[1] if 'Lyrics' in song.lyrics else song.lyrics
                lyrics = re.sub(r'\d*Embed$', '', lyrics).strip()
                
                # Format lyrics with section emojis and consistent spacing
                formatted_lyrics = lyrics
                
                # Replace section headers with emojis and consistent formatting
                section_replacements = {
                    r'\[Chorus\]': '\n\n🎵 **Chorus**\n',
                    r'\[Verse\s*(\d*)\]': r'\n\n🎤 **Verse \1**\n',
                    r'\[Bridge\]': '\n\n🌉 **Bridge**\n',
                    r'\[Pre-Chorus\]': '\n\n🎼 **Pre-Chorus**\n',
                    r'\[Outro\]': '\n\n👋 **Outro**\n',
                    r'\[Intro\]': '\n\n✨ **Intro**\n',
                    r'\[Refrain\]': '\n\n🔄 **Refrain**\n',
                    r'\[Hook\]': '\n\n🪝 **Hook**\n'
                }
                
                # Apply all replacements
                for pattern, replacement in section_replacements.items():
                    formatted_lyrics = re.sub(pattern, replacement, formatted_lyrics, flags=re.IGNORECASE)
                
                # Clean up any excessive newlines
                formatted_lyrics = re.sub(r'\n{3,}', '\n\n', formatted_lyrics)
                
                # Ensure consistent spacing after each line
                formatted_lyrics = '\n'.join(line.strip() for line in formatted_lyrics.split('\n'))
                
                # Create embed with song info and formatted lyrics
                embed = discord.Embed(
                    title=f"🎵 {song.title}",
                    url=song.url if song.url else None,
                    description=f"👤 by {song.artist}\n\n{formatted_lyrics}",
                    color=0x1DB954
                )
                
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send(
                    f"😕 {interaction.user.mention}, couldn't find lyrics for this song!"
                )
        except discord.HTTPException as e:
            # If the message is too long, send a shortened version
            try:
                shortened_lyrics = formatted_lyrics[:1900] + "...\n\n(Lyrics truncated - Click title for full lyrics)"
                embed = discord.Embed(
                    title=f"🎵 {song.title}",
                    url=song.url if song.url else None,
                    description=f"👤 by {song.artist}\n\n{shortened_lyrics}",
                    color=0x1DB954
                )
                await interaction.followup.send(embed=embed)
            except Exception as e:
                print(f"Error sending shortened lyrics: {e}")
                await interaction.followup.send(
                    f"❌ {interaction.user.mention}, the lyrics are too long! Click the title to view them on Genius."
                )
        except Exception as e:
            print(f"Error fetching lyrics: {e}")
            await interaction.followup.send(
                f"❌ {interaction.user.mention}, there was an error fetching the lyrics!"
            )

    @app_commands.command(name="pause", description="Pause or resume the current track")
    async def pause(self, interaction: discord.Interaction):
        """Pauses or resumes the current track."""
        if not interaction.guild.voice_client:
            await interaction.response.send_message(
                f"🤔 {interaction.user.mention}, I'm not playing anything! 🎧"
            )
            return

        try:
            if interaction.guild.voice_client.is_playing():
                interaction.guild.voice_client.pause()
                await interaction.response.send_message(
                    f"⏸️ {interaction.user.mention}, paused the music! ⚓"
                )
            elif interaction.guild.voice_client.is_paused():
                interaction.guild.voice_client.resume()
                await interaction.response.send_message(
                    f"▶️ {interaction.user.mention}, resumed the music! ⛵"
                )
            else:
                await interaction.response.send_message(
                    f"🤔 {interaction.user.mention}, nothing is playing! 🎧"
                )
        except Exception as e:
            print(f"Error in pause command: {e}")
            await interaction.response.send_message(
                f"❌ {interaction.user.mention}, there was an error with the pause command!"
            )

    async def play_next(self, interaction):
        """Plays the next track in the queue."""
        global playlist_queue

        if playlist_queue:
            url = playlist_queue.pop(0)

            with yt_dlp.YoutubeDL({"format": "bestaudio"}) as ydl:
                info = ydl.extract_info(url, download=False)
                audio_url = info["url"]
                # Store current song info
                self.current_song = {
                    'title': info.get('title'),
                }

            # Play the audio
            interaction.guild.voice_client.play(
                discord.FFmpegPCMAudio(
                    audio_url,
                    before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
                ),
                after=lambda e: asyncio.run_coroutine_threadsafe(
                    self.play_next_wrapper(interaction), 
                    interaction.client.loop
                )
            )

            try:
                await interaction.followup.send(
                    f"🎵 Now playing: **{info.get('title')}**! 🍖"
                )
            except discord.NotFound:
                await interaction.channel.send(
                    f"🎵 Now playing: **{info.get('title')}**! 🍖"
                )

    async def play_next_wrapper(self, interaction):
        """Wrapper for play_next to handle the after callback."""
        await self.play_next(interaction)

async def register(bot):
    """Registers the DJ cog with the bot."""
    await bot.add_cog(DJ(bot))
    print("DJ cog registered.")
