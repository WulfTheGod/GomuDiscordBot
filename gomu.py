import discord
from discord.ext import commands
import os
import importlib
from dotenv import load_dotenv

load_dotenv()

# Initialize bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, application_id=1309204697579655168)

async def load_modules():
    """Dynamically loads all feature modules in the 'modules' folder."""
    modules_dir = "./modules"
    for module_name in os.listdir(modules_dir):
        if os.path.isdir(os.path.join(modules_dir, module_name)):
            try:
                module = importlib.import_module(f"modules.{module_name}.main")
                if hasattr(module, "register"):
                    await module.register(bot)
                print(f"Loaded module: {module_name}")
            except Exception as e:
                print(f"Failed to load module {module_name}: {e}")

@bot.event
async def on_ready():
    print(f"Bot is ready! Logged in as {bot.user}")

    # Load modules first
    await load_modules()

    try:
        print("Commands in bot.tree before syncing:")
        for command in bot.tree.get_commands():
            print(f"- {command.name}: {command.description}")

        # Set up guild
        GUILD_ID = 1232664961436745769
        guild = discord.Object(id=GUILD_ID)
        
        # Clear and copy commands
        bot.tree.clear_commands(guild=guild)
        
        # Sync commands globally first
        await bot.tree.sync()
        
        # Then sync to specific guild
        synced = await bot.tree.sync(guild=guild)
        print(f"Synced {len(synced)} command(s) to guild: {GUILD_ID}")
        
        # Print final command list
        print("\nFinal command list:")
        for cmd in bot.tree.get_commands():
            print(f"- {cmd.name}: {cmd.description}")
            
    except Exception as e:
        print(f"Failed to sync commands: {e}")



bot.run(os.getenv("DISCORD_TOKEN"))
