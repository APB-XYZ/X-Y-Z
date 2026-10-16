import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv

# Charger le fichier .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", 0))

intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print(f"❌ Impossible de trouver le serveur avec l'ID {GUILD_ID}")
        await bot.close()
        return

    print(f"🤖 Connecté en tant que {bot.user}. Début de la création des rôles sur '{guild.name}'...\n")

    # 1. Rôles de Sécurité & Onboarding
    security_roles = [
        {"name": "⏳・[Pending Approval]", "color": discord.Color.orange()},
        {"name": "❌・[Denied]", "color": discord.Color.dark_red()},
        {"name": "🚫・[Blacklisted]", "color": discord.Color.from_rgb(20, 20, 20)},
        {"name": "⭐・[Recruit]", "color": discord.Color.gold()},
        {"name": "💀・[Member]", "color": discord.Color.from_rgb(255, 255, 255)}
    ]

    print("--- CRÉATION DES RÔLES DE SÉCURITÉ ---")
    for r_data in security_roles:
        existing = discord.utils.get(guild.roles, name=r_data["name"])
        if not existing:
            role = await guild.create_role(name=r_data["name"], color=r_data["color"], reason="Automatisation - Sécurité Syndicate")
            print(f"✅ Rôle créé : {role.name}")
        else:
            print(f"ℹ️ Existe déjà : {existing.name}")
        await asyncio.sleep(0.4)

    # 2. Matrice des Niveaux (1 à 100)
    levels_matrix = [
        (range(1, 5), "⭐・[Lvl 01-04] Outer Fringe Civilian", discord.Color.light_grey()),
        (range(5, 6), "⭐・[Lvl 05] Syndicate Prospect", discord.Color.gold()),
        (range(6, 15), "⭐・[Lvl 06-14] Street Runner", discord.Color.lighter_grey()),
        (range(15, 16), "🎖️・[Lvl 15] Underground Operative", discord.Color.blue()),
        (range(16, 25), "🎖️・[Lvl 16-24] Block Operative", discord.Color.dark_blue()),
        (range(25, 26), "🛡️・[Lvl 25] Syndicate Specialist", discord.Color.green()),
        (range(26, 40), "🛡️・[Lvl 26-39] District Guardian", discord.Color.dark_green()),
        (range(40, 41), "⚡・[Lvl 40] Sector Vanguard", discord.Color.purple()),
        (range(41, 55), "⚡・[Lvl 41-54] Black Market Operative", discord.Color.dark_purple()),
        (range(55, 56), "🎯・[Lvl 55] Syndicate Veteran", discord.Color.orange()),
        (range(56, 70), "🎯・[Lvl 56-69] Elite Executioner", discord.Color.from_rgb(126, 81, 9)),
        (range(70, 71), "⚔️・[Lvl 70] Syndicate Commander", discord.Color.red()),
        (range(71, 85), "⚔️・[Lvl 71-84] Shadow Strike Lead", discord.Color.from_rgb(100, 30, 22)),
        (range(85, 86), "🔥・[Lvl 85] Mainframe Phantom", discord.Color.from_rgb(230, 126, 34)),
        (range(86, 95), "🔥・[Lvl 86-94] Apex Vanguard", discord.Color.from_rgb(255, 0, 127)),
        (range(95, 96), "💀・[Lvl 95] Syndicate Overlord", discord.Color.from_rgb(155, 89, 182)),
        (range(96, 100), "💀・[Lvl 96-99] Syndicate Prime", discord.Color.from_rgb(74, 35, 90)),
        (range(100, 101), "⚡👑・[Lvl 100] Syndicate Legend", discord.Color.from_rgb(255, 215, 0))
    ]

    print("\n--- CRÉATION DE LA MATRICE DE NIVEAUX (1-100) ---")
    for r_range, name, color in levels_matrix:
        existing = discord.utils.get(guild.roles, name=name)
        if not existing:
            role = await guild.create_role(name=name, color=color, reason="Automatisation - Niveaux Syndicate")
            print(f"✅ Rôle créé : {role.name}")
        else:
            print(f"ℹ️ Existe déjà : {existing.name}")
        await asyncio.sleep(0.4)

    # 3. Divisions & Rôles d'Élite
    extra_roles = [
        {"name": "🏙️・[Financial Expert]", "color": discord.Color.from_rgb(93, 173, 226)},
        {"name": "🌊・[Waterfront Specialist]", "color": discord.Color.from_rgb(72, 201, 176)},
        {"name": "🏎️・[Wheelman]", "color": discord.Color.from_rgb(244, 208, 63)},
        {"name": "🔧・[Armorer & Designer]", "color": discord.Color.from_rgb(235, 152, 78)},
        {"name": "📡・[Intel Scout]", "color": discord.Color.from_rgb(82, 190, 128)},
        {"name": "🎯・[Enforcer Killer]", "color": discord.Color.from_rgb(236, 112, 99)},
        {"name": "🌟・[XYZ Apex Predator]", "color": discord.Color.from_rgb(243, 156, 18)},
        {"name": "🔮・[Syndicate Phantom]", "color": discord.Color.from_rgb(175, 122, 197)},
        {"name": "🎖️・[Task Force Commander]", "color": discord.Color.from_rgb(84, 153, 199)},
        {"name": "⚜️・[XYZ Veteran]", "color": discord.Color.from_rgb(186, 74, 0)},
        {"name": "💤・[Reserve Force]", "color": discord.Color.from_rgb(127, 140, 141)},
        {"name": "🚀・[XYZ Booster]", "color": discord.Color.from_rgb(255, 115, 250)},
        {"name": "🎧・[Frequency DJ]", "color": discord.Color.from_rgb(26, 188, 156)},
        {"name": "👁️‍🗨️・[The Syndicate Oracle]", "color": discord.Color.from_rgb(255, 255, 255)}
    ]

    print("\n--- CRÉATION DES DIVISIONS ET RÔLES D'ÉLITE ---")
    for r_data in extra_roles:
        existing = discord.utils.get(guild.roles, name=r_data["name"])
        if not existing:
            role = await guild.create_role(name=r_data["name"], color=r_data["color"], reason="Automatisation - Divisions Syndicate")
            print(f"✅ Rôle créé : {role.name}")
        else:
            print(f"ℹ️ Existe déjà : {existing.name}")
        await asyncio.sleep(0.4)

    print("\n✨ Opération terminée avec succès ! Tous les rôles ont été injectés.")
    await bot.close()

bot.run(TOKEN)