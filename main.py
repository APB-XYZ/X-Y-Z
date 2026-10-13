import asyncio
import discord
from discord import app_commands
from discord.ext import tasks, commands
import requests
import json
import os
import time
from dotenv import load_dotenv

# Chargement du fichier .env local (ignoré en production sur Koyeb si géré via les secrets du dashboard)
load_dotenv()

# ==========================================
# CONFIGURATION DU TERMINAL X Y Z SYNDICATE
# ==========================================
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", 0))

# IDs DE TES SALONS ET RÔLES (Récupérés depuis les variables d'environnement)
CHANNELS = {
    "membres": int(os.getenv("CHANNEL_MEMBRES", 0)),      
    "core": int(os.getenv("CHANNEL_CORE", 0)),         
    "apb_status": int(os.getenv("CHANNEL_APB_STATUS", 0)),   
    "quantum": int(os.getenv("CHANNEL_QUANTUM", 0)),      
    "welcome": int(os.getenv("CHANNEL_WELCOME", 0)),      
    "ranks": int(os.getenv("CHANNEL_RANKS", 0)),        
    "rules": int(os.getenv("CHANNEL_RULES", 0)),
    "marketplace": int(os.getenv("CHANNEL_MARKETPLACE", 0)),
    "armory_builds": int(os.getenv("CHANNEL_ARMORY_BUILDS", 0))
}

ROLE_IDS = {
    "recruit": int(os.getenv("ROLE_RECRUIT", 0)),      
    "member": int(os.getenv("ROLE_MEMBER", 0))        
}

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

# ==========================================
# BASE DE DONNÉES APB:Db (ARMES AVEC TYPES & MAX SLOTS)
# ==========================================
WEAPON_DATABASE = {
    "N-TEC 5": {"icon": "[0]", "img": "https://apbdb.com/images/items/Weapon_AssaultRifle_NTEC_5.png", "type": "Assault Rifle", "max_slots": 0},
    "N-TEC 5 Stock": {"icon": "[0]", "img": "https://apbdb.com/images/items/Weapon_AssaultRifle_NTEC_5.png", "type": "Assault Rifle", "max_slots": 0},
    "N-TEC 5 Nol Stock": {"icon": "[1]", "img": "https://apbdb.com/images/items/Weapon_AssaultRifle_NTEC_5.png", "type": "Assault Rifle", "max_slots": 1},
    "N-TEC 5 Adeen Stock": {"icon": "[2]", "img": "https://apbdb.com/images/items/Weapon_AssaultRifle_NTEC_5.png", "type": "Assault Rifle", "max_slots": 2},
    "N-TEC 5 'Cops-Bane' Stock": {"icon": "[3]", "img": "https://apbdb.com/images/items/Weapon_AssaultRifle_NTEC_5.png", "type": "Assault Rifle", "max_slots": 3},
    "N-TEC 7 Adeen": {"icon": "[2]", "img": "https://apbdb.com/images/items/Weapon_AssaultRifle_NTEC_5.png", "type": "Assault Rifle", "max_slots": 2},
    "N-TEC 5 Nol": {"icon": "[1]", "img": "https://apbdb.com/images/items/Weapon_AssaultRifle_NTEC_5.png", "type": "Assault Rifle", "max_slots": 1},
    "N-TEC 5 Adeen": {"icon": "[2]", "img": "https://apbdb.com/images/items/Weapon_AssaultRifle_NTEC_5.png", "type": "Assault Rifle", "max_slots": 2},
    "STAR 556": {"icon": "[0]", "img": "https://apbdb.com/images/items/Weapon_AssaultRifle_STAR556.png", "type": "Assault Rifle", "max_slots": 0},
    "STAR 556 R&D I": {"icon": "[1]", "img": "https://apbdb.com/images/items/Weapon_AssaultRifle_STAR556.png", "type": "Assault Rifle", "max_slots": 1},
    "STAR 556 R&D II": {"icon": "[2]", "img": "https://apbdb.com/images/items/Weapon_AssaultRifle_STAR556.png", "type": "Assault Rifle", "max_slots": 2},
    "N-TEC 5 Dvah": {"icon": "[3]", "img": "https://apbdb.com/images/items/Weapon_AssaultRifle_NTEC_5.png", "type": "Assault Rifle", "max_slots": 3},
    "STAR 556 R&D III": {"icon": "[3]", "img": "https://apbdb.com/images/items/Weapon_AssaultRifle_STAR556.png", "type": "Assault Rifle", "max_slots": 3},
    "N-TEC 5 Dvah Stock": {"icon": "[3]", "img": "https://apbdb.com/images/items/Weapon_AssaultRifle_NTEC_5.png", "type": "Assault Rifle", "max_slots": 3},
}

MODS_DATABASE = {
    "Hunting Sight 3": {"icon": "👁️‍🗨️", "color_tag": "🟢 [Accuracy / Scope]", "img": "https://apbdb.com/images/items/Mod_HuntingSight3.png"},
    "Improved Rifling 3": {"icon": "📈", "color_tag": "🔵 [Effective Range]", "img": "https://apbdb.com/images/items/Mod_ImprovedRifling3.png"},
    "Magazine Pull 3": {"icon": "🔄", "color_tag": "🔵 [Reload Speed]", "img": "https://apbdb.com/images/items/Mod_MagPull3.png"},
    "Cooling Jacket 3": {"icon": "❄️", "color_tag": "🟠 [Heat Recovery]", "img": "https://apbdb.com/images/items/Mod_CoolingJacket3.png"},
    "Extended Magazine 3": {"icon": "🔋", "color_tag": "🟣 [Ammo Capacity]", "img": "https://apbdb.com/images/items/Mod_ExtendedMag3.png"},
    "Mobility Sling": {"icon": "🏃", "color_tag": "🟢 [Movement Speed]", "img": "https://apbdb.com/images/items/Mod_MobilitySling.png"},
    "Tethered Stop": {"icon": "🛑", "color_tag": "🔴 [Control / Firing]", "img": "https://apbdb.com/images/items/Mod_TetheredStop.png"},
    "Bane 3": {"icon": "⚡", "color_tag": "🟠 [Vehicle Damage]", "img": "https://apbdb.com/images/items/Mod_Bane3.png"},
    "Heavy Barrel 3": {"icon": "🪵", "color_tag": "🔴 [Recoil & Damage]", "img": "https://apbdb.com/images/items/Mod_HeavyBarrel3.png"},
    "Rapid Fire": {"icon": "⏩", "color_tag": "🟠 [Rate of Fire]", "img": "https://apbdb.com/images/items/Mod_RapidFire.png"},
    "Bottomless Magazine": {"icon": "♾️", "color_tag": "🟣 [Max Ammo Pool]", "img": "https://apbdb.com/images/items/Mod_BottomlessMag.png"},
    "Bandolier": {"icon": "🎒", "color_tag": "🔵 [Carrying Capacity]", "img": "https://apbdb.com/images/items/Mod_Bandolier.png"},
    "Reflex Sight": {"icon": "⭕", "color_tag": "🟢 [CQC Precision]", "img": "https://apbdb.com/images/items/Mod_ReflexSight.png"},
    "Clumping": {"icon": "🎯", "color_tag": "🔵 [Spread Reduction]", "img": "https://apbdb.com/images/items/Mod_Clumping.png"}
}

WEAPON_LIST = list(WEAPON_DATABASE.keys())
MODS_LIST = list(MODS_DATABASE.keys())

# ==========================================
# SYSTÈMES INTERACTIFS ARMORY & MARKETPLACE
# ==========================================

class ArmoryNotesModal(discord.ui.Modal, title="X Y Z Syndicate // Tactical Assessment"):
    def __init__(self, weapon: str, max_slots: int, mod1: str, mod2: str, mod3: str):
        super().__init__()
        self.weapon = weapon
        self.max_slots = max_slots
        self.mod1 = mod1
        self.mod2 = mod2
        self.mod3 = mod3

    tactical_notes = discord.ui.TextInput(
        label="Tactical Playstyle & Recoil Assessment",
        placeholder="e.g. Mid-range burst control, optimal mobility, great recoil management.",
        style=discord.TextStyle.paragraph,
        min_length=5,
        max_length=300,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        notes = self.tactical_notes.value.strip()
        user = interaction.user

        w_data = WEAPON_DATABASE.get(self.weapon, {"icon": "🔫", "img": None, "type": "Firearm", "max_slots": 3})
        w_icon, w_img, w_type = w_data["icon"], w_data["img"], w_data["type"]

        m1_data = MODS_DATABASE.get(self.mod1, {"icon": "⚙️", "color_tag": "Standard"}) if self.mod1 else None
        m2_data = MODS_DATABASE.get(self.mod2, {"icon": "⚙️", "color_tag": "Standard"}) if self.mod2 else None
        m3_data = MODS_DATABASE.get(self.mod3, {"icon": "⚙️", "color_tag": "Standard"}) if self.mod3 else None

        mods_text = f"🔹 **Slot 01** ➔ {m1_data['icon']} `{self.mod1}` *({m1_data['color_tag']})*\n" if self.mod1 else "🔹 **Slot 01** ➔ *[Not Equipped]*\n"
        if self.max_slots >= 2:
            mods_text += f"🔹 **Slot 02** ➔ {m2_data['icon']} `{self.mod2}` *({m2_data['color_tag']})*\n" if self.mod2 else "🔹 **Slot 02** ➔ *[Not Equipped]*\n"
        if self.max_slots >= 3:
            mods_text += f"🔹 **Slot 03** ➔ {m3_data['icon']} `{self.mod3}` *({m3_data['color_tag']})*\n" if self.mod3 else "🔹 **Slot 03** ➔ *[Not Equipped]*\n"

        embed = discord.Embed(
            title="⚡ X Y Z // SAN PARO TACTICAL ARMORY BUILD ⚡",
            description=(
                f"> **DATABASE SYNC // APB:Db SECURE PRESET**\n"
                f"> *Encrypted weapon configuration deployed across Citadel EU districts.*\n\n"
                f"### 🎯 **FIREARM SPECIFICATION**\n"
                f"```ini\n"
                f"[ Model ] : {self.weapon}\n"
                f"[ Class ] : {w_type}\n"
                f"[ Allowed Slots ] : {self.max_slots} Slots\n"
                f"[ Author ] : {user.name}\n"
                f"```\n"
                f"### ⚙️ **MODIFICATION MATRIX**\n"
                f"{mods_text}\n"
                f"### 📝 **TACTICAL & RECOIL ASSESSMENT**\n"
                f"```yaml\n{notes}\n```"
            ),
            color=0xD4AF37,
            timestamp=discord.utils.utcnow()
        )
        
        if w_img:
            embed.set_thumbnail(url=w_img)
        else:
            embed.set_thumbnail(url=user.display_avatar.url)

        embed.set_footer(text=f"Operative ID: {user.id} • X Y Z Syndicate Armory Core", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)

        target_channel = interaction.guild.get_channel(CHANNELS["armory_builds"]) or interaction.channel
        await target_channel.send(content=f"🎯 **New Armory Build successfully deployed by** {user.mention}", embed=embed)
        
        await interaction.response.send_message(
            "✅ **Build compiled and transmitted!** Your configuration is now live in `🛠️│armory-builds`.",
            ephemeral=True
        )

class ArmorySelectDropdowns(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
        self.selected_weapon = WEAPON_LIST[0]
        self.max_slots = WEAPON_DATABASE[self.selected_weapon]["max_slots"]
        self.selected_mod1 = None
        self.selected_mod2 = None
        self.selected_mod3 = None

        self.update_components()

    def update_components(self):
        self.clear_items()
        self.max_slots = WEAPON_DATABASE[self.selected_weapon]["max_slots"]

        weapon_options = [
            discord.SelectOption(
                label=w, 
                value=w, 
                description=f"Type: {WEAPON_DATABASE[w]['type']} | Max Slots: {WEAPON_DATABASE[w]['max_slots']}", 
                default=(w == self.selected_weapon)
            ) 
            for w in WEAPON_LIST
        ]

        weapon_select = discord.ui.Select(
            placeholder="🔫 Select Firearm (APB Database)...",
            min_values=1, max_values=1,
            options=weapon_options[:25],
            custom_id="select_weapon_xyz",
            row=0
        )
        weapon_select.callback = self.weapon_callback
        self.add_item(weapon_select)

        options_mod1 = [
            discord.SelectOption(label=m, value=m, description=MODS_DATABASE[m]["color_tag"], default=(m == self.selected_mod1))
            for m in MODS_LIST if m != self.selected_mod2 and m != self.selected_mod3
        ]
        mod1_select = discord.ui.Select(
            placeholder="⚙️ Select Slot 1 Modification...",
            min_values=1, max_values=1,
            options=options_mod1[:25] if options_mod1 else [discord.SelectOption(label="None available", value="None")],
            custom_id="select_mod1_xyz",
            row=1
        )
        mod1_select.callback = self.mod1_callback
        self.add_item(mod1_select)

        if self.max_slots >= 2:
            options_mod2 = [
                discord.SelectOption(label=m, value=m, description=MODS_DATABASE[m]["color_tag"], default=(m == self.selected_mod2))
                for m in MODS_LIST if m != self.selected_mod1 and m != self.selected_mod3
            ]
            mod2_select = discord.ui.Select(
                placeholder="⚙️ Select Slot 2 Modification...",
                min_values=1, max_values=1,
                options=options_mod2[:25] if options_mod2 else [discord.SelectOption(label="None available", value="None")],
                custom_id="select_mod2_xyz",
                row=2
            )
            mod2_select.callback = self.mod2_callback
            self.add_item(mod2_select)
        else:
            self.selected_mod2 = None

        if self.max_slots >= 3:
            options_mod3 = [
                discord.SelectOption(label=m, value=m, description=MODS_DATABASE[m]["color_tag"], default=(m == self.selected_mod3))
                for m in MODS_LIST if m != self.selected_mod1 and m != self.selected_mod2
            ]
            mod3_select = discord.ui.Select(
                placeholder="⚙️ Select Slot 3 Modification...",
                min_values=1, max_values=1,
                options=options_mod3[:25] if options_mod3 else [discord.SelectOption(label="None available", value="None")],
                custom_id="select_mod3_xyz",
                row=3
            )
            mod3_select.callback = self.mod3_callback
            self.add_item(mod3_select)
        else:
            self.selected_mod3 = None

        finalize_button = discord.ui.Button(
            label=f"Publish Build ({self.max_slots} Slots Allowed)", 
            style=discord.ButtonStyle.success, 
            custom_id="finalize_build_btn", 
            emoji="🚀", 
            row=4
        )
        finalize_button.callback = self.finalize_build
        self.add_item(finalize_button)

    async def weapon_callback(self, interaction: discord.Interaction):
        self.selected_weapon = interaction.data['values'][0]
        self.update_components()
        await interaction.response.edit_message(view=self)

    async def mod1_callback(self, interaction: discord.Interaction):
        self.selected_mod1 = interaction.data['values'][0]
        self.update_components()
        await interaction.response.edit_message(view=self)

    async def mod2_callback(self, interaction: discord.Interaction):
        self.selected_mod2 = interaction.data['values'][0]
        self.update_components()
        await interaction.response.edit_message(view=self)

    async def mod3_callback(self, interaction: discord.Interaction):
        self.selected_mod3 = interaction.data['values'][0]
        self.update_components()
        await interaction.response.edit_message(view=self)

    async def finalize_build(self, interaction: discord.Interaction):
        if self.max_slots > 0 and not self.selected_mod1:
            await interaction.response.send_message("❌ **Error:** Slot 1 modification is required.", ephemeral=True)
            return
        if self.max_slots >= 2 and not self.selected_mod2:
            await interaction.response.send_message(f"❌ **Error:** This firearm allows {self.max_slots} slots. Please equip Slot 2.", ephemeral=True)
            return
        if self.max_slots >= 3 and not self.selected_mod3:
            await interaction.response.send_message(f"❌ **Error:** This firearm allows {self.max_slots} slots. Please equip Slot 3.", ephemeral=True)
            return

        await interaction.response.send_modal(ArmoryNotesModal(
            weapon=self.selected_weapon,
            max_slots=self.max_slots,
            mod1=self.selected_mod1 if self.max_slots > 0 else None, 
            mod2=self.selected_mod2 if self.max_slots >= 2 else None,
            mod3=self.selected_mod3 if self.max_slots >= 3 else None
        ))

class ArmoryView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Initialize Armory Studio Terminal", style=discord.ButtonStyle.primary, custom_id="open_armory_studio_xyz", emoji="🛠️")
    async def open_studio(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🛠️ X Y Z // INTERACTIVE WEAPON STUDIO TERMINAL",
            description=(
                f"> **SECURE ACCESS // APB:Db DATABASE LOADED**\n"
                f"> *Configure your loadout below. Each firearm clearly displays its weapon class and enforces its official in-game maximum slot limit.*\n\n"
                f"---\n"
                f"> *« Precision in selection yields absolute dominance in San Paro districts. »*"
            ),
            color=0xD4AF37
        )
        embed.set_footer(text="X Y Z Syndicate Encryption Protocol • Citadel EU")
        await interaction.response.send_message(embed=embed, view=ArmorySelectDropdowns(), ephemeral=True)


class MarketplaceModal(discord.ui.Modal, title="X Y Z Syndicate // Marketplace Terminal"):
    trade_type = discord.ui.TextInput(label="Offer Type (SELL / BUY / TRADE)", placeholder="e.g. SELL or BUY", min_length=3, max_length=15, required=True)
    item_name = discord.ui.TextInput(label="Item / Weapon / Vehicle / Symbol Name", placeholder="e.g. N-TEC 5 Tactical, Juggernaut...", min_length=2, max_length=100, required=True)
    price = discord.ui.TextInput(label="Price / Trade Terms (In-Game)", placeholder="e.g. $50,000 Cash or trade for...", min_length=2, max_length=50, required=True)
    description = discord.ui.TextInput(label="Additional Details / Contact Info", placeholder="e.g. Contact me via Discord DM or in-game on Citadel.", style=discord.TextStyle.paragraph, min_length=5, max_length=300, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        t_type = self.trade_type.value.strip().upper()
        item = self.item_name.value.strip()
        cost = self.price.value.strip()
        desc = self.description.value.strip()
        user = interaction.user

        if "SELL" in t_type or "VENTE" in t_type:
            color = 0x00FF66
            badge = "🟢 [COMMODITY FOR SALE]"
        elif "BUY" in t_type or "ACHAT" in t_type:
            color = 0x00CCFF
            badge = "🔵 [WANTED / BUYING]"
        else:
            color = 0xD4AF37
            badge = "🟡 [EXCHANGE / TRADE]"

        embed = discord.Embed(
            title=f"⚡ MARKETPLACE TERMINAL // {badge} ⚡",
            description=(
                f"> **SAN PARO SECURE NETWORK**\n"
                f"> *New listing registered on the syndicate trade terminal.*\n\n"
                f"### 📦 **LISTING DETAILS**\n"
                f"- **Target Item:** `{item}`\n"
                f"- **Price / Value:** `{cost}`\n"
                f"- **Operative:** {user.mention} (`{user.name}`)\n\n"
                f"### 📝 **OPERATIVE NOTES**\n"
                f"```yaml\n{desc}\n```"
            ),
            color=color,
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text="X Y Z Syndicate Marketplace • San Paro EU Citadel", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)

        target_channel = interaction.guild.get_channel(CHANNELS["marketplace"]) or interaction.channel
        await target_channel.send(content=f"🔔 **New Marketplace listing by** {user.mention}", embed=embed)
        
        await interaction.response.send_message(
            "✅ **Transmission successful!** Your listing has been published on the San Paro Marketplace.",
            ephemeral=True
        )

class MarketplaceView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Publish Listing / Request", style=discord.ButtonStyle.success, custom_id="open_marketplace_modal_xyz", emoji="🛒")
    async def open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(MarketplaceModal())

class VerificationModal(discord.ui.Modal, title="X Y Z Syndicate // Final Protocol"):
    apb_pseudo = discord.ui.TextInput(
        label="Enter your APB Reloaded In-Game Name",
        placeholder="e.g. CriminalMaster",
        min_length=2,
        max_length=32,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user
        pseudo = self.apb_pseudo.value.strip()

        recruit_role = guild.get_role(ROLE_IDS["recruit"])
        member_role = guild.get_role(ROLE_IDS["member"])

        try:
            await member.edit(nick=pseudo)
        except discord.Forbidden:
            pass 

        if recruit_role and recruit_role in member.roles:
            await member.remove_roles(recruit_role)
        if member_role and member_role not in member.roles:
            await member.add_roles(member_role)

        await interaction.response.send_message(
            f"✅ **Protocol Completed!** Callsign registered as **{pseudo}**. "
            f"You are now officially a validated syndicate member. Welcome to the core.",
            ephemeral=True
        )

        try:
            disabled_view = VerificationView(completed=True)
            await interaction.message.edit(view=disabled_view)
        except Exception:
            pass

class VerificationView(discord.ui.View):
    def __init__(self, completed=False):
        super().__init__(timeout=None)
        if completed:
            for child in self.children:
                child.disabled = True
                child.label = "Registration Completed"
                child.style = discord.ButtonStyle.secondary

    @discord.ui.button(label="Accept Rules & Set APB Nickname", style=discord.ButtonStyle.success, custom_id="verify_rules_xyz", emoji="⚡")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(VerificationModal())

class RanksOnboardingView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Next: Rules ➡️", style=discord.ButtonStyle.primary, custom_id="ranks_to_rules_xyz", emoji="📜")
    async def next_to_rules(self, interaction: discord.Interaction, button: discord.ui.Button):
        rules_channel = interaction.guild.get_channel(CHANNELS["rules"])
        rules_mention = rules_channel.mention if rules_channel else "#rules"
        
        embed_dm = discord.Embed(
            title="⚡ X Y Z // ONBOARDING: STEP 2 (RULES) ⚡",
            description=(
                f"> **SECURE TRANSMISSION // ACCESS GRANTED**\n"
                f"> *You have reviewed the hierarchy. Now, proceed to {rules_mention} to read our core regulations and validate your final clearance.*\n\n"
                "---\n"
                f"> *« Discipline and mutual respect forge our strength. »*"
            ),
            color=0xD4AF37,
            timestamp=discord.utils.utcnow()
        )
        await interaction.response.send_message(embed=embed_dm, ephemeral=True)

class XYZBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        guild_obj = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild_obj)
        await self.tree.sync(guild=guild_obj)
        self.add_view(VerificationView())
        self.add_view(RanksOnboardingView())
        self.add_view(MarketplaceView())
        self.add_view(ArmoryView())
        print("⚡ [DISCORD] Commandes Slash et vues persistantes synchronisées.")

client = XYZBot()

@client.event
async def on_ready():
    print(f"🤖 X Y Z Syndicate Bot connecté et opérationnel en tant que {client.user} !")
    with open("core_status.json", "w") as f:
        json.dump({"status": "Online"}, f)
        
    if not update_cluster_stats.is_running():
        update_cluster_stats.start()

@client.event
async def on_member_join(member: discord.Member):
    if member.guild.id != GUILD_ID:
        return

    recruit_role = member.guild.get_role(ROLE_IDS["recruit"])
    if recruit_role:
        try:
            await member.add_roles(recruit_role)
        except Exception as e:
            print(f"⚠️ [ROLE ERROR] Impossible d'attribuer le rôle recrue : {e}")

    welcome_channel = member.guild.get_channel(CHANNELS["welcome"])
    ranks_channel = member.guild.get_channel(CHANNELS["ranks"])
    rules_channel = member.guild.get_channel(CHANNELS["rules"])
    
    ranks_mention = ranks_channel.mention if ranks_channel else "#ranks"
    rules_mention = rules_channel.mention if rules_channel else "#rules"

    if welcome_channel:
        embed_public = discord.Embed(
            title="⚡ NEW OPERATIVE CONNECTED TO MAINFRAME ⚡",
            description=(
                f"> **QUANTUM LINK // INITIALIZING RECRUIT PROTOCOL**\n\n"
                f"Attention operatives, {member.mention} has successfully breached the network perimeter and joined the **X Y Z // Syndicate**.\n\n"
                f"```ansi\n"
                f" [2;33m[STATUS] ➔ Assigned Rank: [Recruit]\n"
                f" [2;33m[TARGET] ➔ Complete Onboarding & Verification\n"
                f"```\n\n"
                f"A secure direct briefing has been transmitted to your private terminal. Follow the instructions to claim your operational status."
            ),
            color=0xD4AF37,
            timestamp=discord.utils.utcnow()
        )
        embed_public.set_thumbnail(url=member.display_avatar.url)
        embed_public.set_footer(text=f"Operative ID: {member.id} | X Y Z Syndicate Core", icon_url=member.guild.icon.url if member.guild.icon else None)
        
        await welcome_channel.send(content=f"⚠️ **New Arrival Alert:** {member.mention}", embed=embed_public)

    try:
        embed_dm = discord.Embed(
            title="⚡ X Y Z // SECURE ONBOARDING BRIEFING ⚡",
            description=(
                f"> **ENCRYPTED CHANNEL // ESTABLISHED**\n"
                f"> *Welcome {member.name} to the syndicate infrastructure. To integrate fully and unlock all operational districts, complete the following protocol steps:* \n\n"
                "---\n\n"
                f"### 🎯 **STEP 01: EXPLORE THE HIERARCHY**\n"
                f"- Head over to {ranks_mention} to study our ranks, divisions, and command structure.\n\n"
                f"### 📜 **STEP 02: REVIEW REGULATIONS**\n"
                f"- Proceed to {rules_mention} to read our syndicate rules and code of conduct.\n\n"
                f"### ⚡ **STEP 03: VERIFICATION & CALLSIGN**\n"
                f"- Accept the rules via the verification button in {rules_mention} and enter your official **APB Reloaded** in-game name to finalize your membership.\n\n"
                "---\n"
                f"> *« Know your rank, honor your callsign, dominate San Paro. »*"
            ),
            color=0xD4AF37,
            timestamp=discord.utils.utcnow()
        )
        embed_dm.set_footer(text="X Y Z Syndicate Security Core")
        await member.send(embed=embed_dm)
    except discord.Forbidden:
        print(f"⚠️ [DM ERROR] Impossible d'envoyer un message privé à {member.name}.")

def fetch_syndicate_data():
    data_out = {"core_text": "Online 🟢", "apb_text": "Online 🟢", "quantum_text": "Secured 🔒"}
    try:
        if os.path.exists("core_status.json"):
            data_out["core_text"] = "Online 🟢"
        else:
            data_out["core_text"] = "Offline 🔴"
    except:
        data_out["core_text"] = "Online 🟢"

    try:
        res_apb = requests.get("https://apbreloaded.gamersfirst.com/api/serverstatus", timeout=2.0)
        if res_apb.ok:
            apb_json = res_apb.json()
            is_online = str(apb_json.get("status", "online")).lower() == "online"
            data_out["apb_text"] = "Online 🟢" if is_online else "Offline 🔴"
        else:
            data_out["apb_text"] = "Online 🟢"
    except:
        data_out["apb_text"] = "Online 🟢"

    return data_out

@tasks.loop(seconds=15)
async def update_cluster_stats():
    guild = client.get_guild(GUILD_ID)
    if not guild:
        return

    data = await asyncio.to_thread(fetch_syndicate_data)
    total_members = guild.member_count

    new_names = {
        "membres": f"👥│Members : {total_members:,}",
        "core": f"🟢│XYZ Core : {data['core_text']}",
        "apb_status": f"🌐│APB Server : {data['apb_text']}",
        "quantum": f"⚡│Quantum Link : {data['quantum_text']}"
    }

    for key, channel_id in CHANNELS.items():
        if key in ["welcome", "ranks", "rules", "marketplace", "armory_builds"]:
            continue
        channel = guild.get_channel(channel_id)
        if channel and channel.name != new_names[key]:
            try:
                await channel.edit(name=new_names[key])
                await asyncio.sleep(1)
            except discord.HTTPException as e:
                print(f"⚠️ [DISCORD] Rate Limit ou Erreur sur {key}: {e}")
            except Exception as e:
                print(f"❌ [DISCORD] Erreur salon {key}: {e}")

@update_cluster_stats.before_loop
async def before_update():
    await client.wait_until_ready()

# ==========================================
# COMMANDES DU DASHBOARD ET ARMURERIE
# ==========================================

@client.tree.command(name="xyz-status", description="Displays the real-time tactical status of the X Y Z syndicate.")
async def slash_xyz_status(interaction: discord.Interaction):
    await interaction.response.defer()

    data = await asyncio.to_thread(fetch_syndicate_data)
    
    embed = discord.Embed(
        title="⚡ X Y Z // Syndicate - Tactical Status",
        color=0xD4AF37,
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(name="XYZ Core", value=data["core_text"], inline=True)
    embed.add_field(name="APB Server Status", value=data["apb_text"], inline=True)
    embed.add_field(name="Quantum Link", value=data["quantum_text"], inline=True)
    embed.add_field(name="Total Operatives", value=str(interaction.guild.member_count), inline=False)
    
    embed.set_footer(text="San Paro Operations - X Y Z Syndicate")
    await interaction.followup.send(embed=embed)


@client.tree.command(name="updatearmory", description="[ADMIN] Publishes the official armory build studio interface.")
@app_commands.checks.has_permissions(administrator=True)
async def slash_updatearmory(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🛠️ X Y Z // SAN PARO ARMORY & BUILDS STUDIO 🛠️",
        description=(
            "> **TACTICAL ARMAMENT // APB:Db DATABASE INTEGRATION**\n"
            "> *Welcome to the syndicate elite armory studio. Deploy weapon presets, configure core modifications, "
            "and optimize your combat loadout for Citadel EU district dominance.*\n\n"
            "---\n\n"
            "### ⚙️ **OPERATIONAL PROTOCOL**\n"
            "- Click **`Initialize Armory Studio Terminal`** below to open the secure selection interface.\n"
            "- Pick your firearm (each weapon enforces its official in-game maximum slot limit).\n"
            "- Assign your modifications (duplicate selections across slots are automatically prevented).\n"
            "- Finalize with your tactical playstyle assessment and broadcast to the network.\n\n"
            "---\n"
            "> *« Superior firepower and flawless preparation are the keys to controlling San Paro. »*"
        ),
        color=0xD4AF37,
        timestamp=discord.utils.utcnow()
    )
    embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
    embed.set_footer(text="San Paro Armory Core • X Y Z Syndicate Infrastructure")
    
    await interaction.response.send_message("✅ Armory Build Studio terminal successfully deployed.", ephemeral=True)
    await interaction.channel.send(embed=embed, view=ArmoryView())


@client.tree.command(name="updatemarket", description="[ADMIN] Publishes the official syndicate marketplace interface.")
@app_commands.checks.has_permissions(administrator=True)
async def slash_updatemarket(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚡ X Y Z // SAN PARO MARKETPLACE ⚡",
        description=(
            "> **SECURE TRADE TRANSMISSION // CITADEL (EU)**\n"
            "> *Welcome to the official syndicate marketplace. Use this secure terminal to buy, sell, or trade weapons, "
            "modifications, vehicles, and custom symbols across the streets of San Paro.*\n\n"
            "---\n\n"
            "### 💼 **HOW TO OPERATE**\n"
            "- Click the **`Publish Listing / Request`** button below to open the secure trade modal.\n"
            "- Fill in whether you are posting a **SELL**, **BUY**, or **TRADE** offer.\n"
            "- Specify the item name, your price in cash or trades, and your contact instructions.\n\n"
            "---\n"
            "> *« Business is business, and the syndicate always takes its cut. Keep transactions clean. »*"
        ),
        color=0xD4AF37,
        timestamp=discord.utils.utcnow()
    )
    embed.set_footer(text="San Paro Commercial Core • X Y Z Syndicate")
    
    await interaction.response.send_message("✅ Marketplace interface successfully generated.", ephemeral=True)
    await interaction.channel.send(embed=embed, view=MarketplaceView())


@client.tree.command(name="xyz-ping", description="Measures bot core telemetry response time.")
async def slash_xyz_ping(interaction: discord.Interaction):
    start_time = time.monotonic()
    await interaction.response.send_message("⚡ Pinging Quantum Core...", ephemeral=True)
    end_time = time.monotonic()
    latency = round((end_time - start_time) * 1000)
    api_latency = round(client.latency * 1000)
    
    embed = discord.Embed(
        title="⚡ TELEMETRY // PING METRICS",
        description=f"```ansi\n [2;33m[ROUNDTRIP] ➔ {latency}ms\n[API LATENCY] ➔ {api_latency}ms [0m```",
        color=0xD4AF37
    )
    await interaction.edit_original_response(content=None, embed=embed)


@client.tree.command(name="xyz-serverinfo", description="Displays server technical specifications.")
async def slash_xyz_serverinfo(interaction: discord.Interaction):
    guild = interaction.guild
    embed = discord.Embed(
        title=f"⚡ {guild.name} // SERVER TELEMETRY",
        description=f"> **OWNER:** {guild.owner.mention}\n> **CREATED:** <t:{int(guild.created_at.timestamp())}:R>",
        color=0xD4AF37,
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(name="👑 Owner", value=guild.owner.mention, inline=True)
    embed.add_field(name="🛡️ Roles", value=str(len(guild.roles)), inline=True)
    embed.add_field(name="💬 Channels", value=str(len(guild.text_channels) + len(guild.voice_channels)), inline=True)
    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
    embed.set_footer(text="X Y Z Syndicate Infrastructure")
    await interaction.response.send_message(embed=embed)


@client.tree.command(name="xyz-lock", description="[ADMIN] Locks down the current channel.")
@app_commands.checks.has_permissions(administrator=True)
async def slash_xyz_lock(interaction: discord.Interaction):
    channel = interaction.channel
    overwrite = channel.overwrites_for(interaction.guild.default_role)
    overwrite.send_messages = False
    await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
    
    embed = discord.Embed(
        title="🔒 CHANNEL LOCKED // SECURITY PROTOCOL",
        description=f"Operational transmissions in {channel.mention} have been suspended by command authority.",
        color=discord.Color.dark_red()
    )
    await interaction.response.send_message(embed=embed)


@client.tree.command(name="xyz-unlock", description="[ADMIN] Restores channel transmissions.")
@app_commands.checks.has_permissions(administrator=True)
async def slash_xyz_unlock(interaction: discord.Interaction):
    channel = interaction.channel
    overwrite = channel.overwrites_for(interaction.guild.default_role)
    overwrite.send_messages = True
    await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
    
    embed = discord.Embed(
        title="🔓 CHANNEL UNLOCKED // TRANSMISSION RESTORED",
        description=f"Normal communication channels in {channel.mention} are back online.",
        color=0xD4AF37
    )
    await interaction.response.send_message(embed=embed)


@client.tree.command(name="xyz-purge", description="[ADMIN] Purges a specified number of messages.")
@app_commands.describe(amount="Number of messages to delete (1-100)")
@app_commands.checks.has_permissions(administrator=True)
async def slash_xyz_purge(interaction: discord.Interaction, amount: int):
    if amount < 1 or amount > 100:
        await interaction.response.send_message("❌ Error: Choose between 1 and 100.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🧹 Successfully wiped `{len(deleted)}` messages.", ephemeral=True)


# ==========================================
# GESTION DES RÈGLES ET DU RÉPERTOIRE
# ==========================================

@client.tree.command(name="updateranks", description="Publishes the official syndicate ranks directory.")
@app_commands.checks.has_permissions(administrator=True)
async def slash_updateranks(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚡ X Y Z // SYNDICATE DIRECTORY ⚡",
        description=(
            "> **SECURE TRANSMISSION // QUANTUM LINK: SECURED**\n"
            "> *Welcome to the official hierarchy of the syndicate. Discipline, operational loyalty, "
            "and absolute dominance over the streets of San Paro define your worth within our infrastructure.*\n\n"
            "---\n\n"
            "### 👑 SUPREME COMMAND & SYSTEM\n"
            "- **`👑・[Owner]`** — Absolute authority and supreme administration controlling the core vision.\n"
            "- **`⚜️・[XYZ Architect]`** — Mastermind behind technological infrastructure and telemetry.\n"
            "- **`🔥・[Leader]`** — Supreme commander of clan operations and strategic decisions.\n"
            "- **`🛡️・[Officer]`** — Elite framework in charge of moderation and recruit training.\n"
            "- **`💻・[XYZ Bot]`** — Autonomous system entity managing live telemetry and security.\n\n"
            "---\n\n"
            "### 💀 SYNDICATE CORE (APB LORE)\n"
            "- **`💀・[Member]`** — Fully validated official operative dedicated to San Paro.\n"
            "- **`⭐・[Recruit]`** — Candidate undergoing strict probation under officer supervision.\n\n"
            "---\n\n"
            "### ⚔️ TACTICAL DIVISIONS\n"
            "- **`🏙️・[Financial Expert]`** — Long-range combat specialist in Financial.\n"
            "- **`🌊・[Waterfront Specialist]`** — Close-quarters urban combat expert in Waterfront.\n"
            "- **`🏎️・[Wheelman]`** — Elite driver for high-speed getaways and positioning.\n"
            "- **`🔧・[Armorer & Designer]`** — Master of vehicle styling, symbols, and gear.\n"
            "- **`📡・[Intel Scout]`** — Recon specialist for tracking and telemetry.\n"
            "- **`🎯・[Enforcer Killer]`** — High-tier PvP elimination specialist.\n\n"
            "---\n\n"
            "### 🏆 ACHIEVEMENTS & ELITE RANKS\n"
            "- **`🌟・[XYZ Apex Predator]`** — Supreme decoration awarded exclusively to champions of internal PvP tournaments and clan events.\n"
            "- **`🔮・[Syndicate Phantom]`** — Elite title earned through high-risk infiltration, sabotage, and covert operations.\n"
            "- **`🎖️・[Task Force Commander]`** — Temporary or permanent command rank assigned to lead major district campaigns.\n"
            "- **`⚜️・[XYZ Veteran]`** — Respected long-standing member valued for deep combat experience across San Paro eras.\n"
            "- **`💤・[Reserve Force]`** — Trusted veterans currently on tactical standby or resting from active duty.\n\n"
            "---\n\n"
            "### ⭐ COMMUNITY & PERKS\n"
            "- **`🚀・[XYZ Booster]`** — Active supporters propelling the server infrastructure and boosting community growth.\n"
            "- **`🎧・[Frequency DJ]`** — Sound maestro authorized to manage audio streams and custom music vibes in `#frequency`.\n"
            "- **`🚫・[Blacklisted]`** — Restricted security cell.\n"
            "- **`👁️‍🗨️・[The Syndicate Oracle]`** — Unique supreme entity embodying the ultimate lore, core identity, and eternal vision.\n\n"
            "---\n"
            "> *« Know your rank, honor your callsign. Click below to proceed to the rules. »*"
        ),
        color=0xD4AF37
    )
    
    await interaction.response.send_message("✅ Répertoire des rangs généré avec succès.", ephemeral=True)
    await interaction.channel.send(embed=embed, view=RanksOnboardingView())


@app_commands.checks.has_permissions(administrator=True)
@client.tree.command(name="updaterules", description="Publishes the official syndicate rules.")
async def slash_updaterules(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚡ X Y Z // SYNDICATE PROTOCOLS & RULES ⚡",
        description=(
            "> **SECURITY DIRECTIVE // MANDATORY COMPLIANCE**\n"
            "> *Welcome to the core rules of the syndicate. By accepting these protocols, you commit to maintaining discipline, respect, and absolute synergy within our infrastructure.*\n\n"
            "---\n\n"
            "### 🛡️ **01. RESPECT & ATMOSPHERE**\n"
            "- Mutual respect is mandatory between all operatives, regardless of rank or background.\n"
            "- Keep a positive mood, maintain good vibes, and enjoy the community. Toxic behavior, harassment, or severe drama will lead to immediate isolation (`[Blacklisted]`).\n\n"
            "### 🎮 **02. FREEDOM OF PLAY & SQUADS**\n"
            "- Operatives are entirely **free to play however they want** — whether grouped in squads or solo across the districts of San Paro.\n"
            "- Teamwork is encouraged for district dominance, but mandatory grouping is never enforced. Play at your own pace and style.\n\n"
            "### ⚡ **03. REGISTRATION & VERIFICATION**\n"
            "- Before becoming a full member and unlocking all operational channels, you **must accept these rules** and register your official **APB Reloaded in-game callsign** using the button below.\n\n"
            "---\n"
            "> *« By clicking the button below, you swear loyalty to the syndicate code and validate your operational clearance. »*"
        ),
        color=0xD4AF37
    )
    
    await interaction.response.send_message("✅ Règlement du serveur généré avec succès.", ephemeral=True)
    await interaction.channel.send(embed=embed, view=VerificationView())

@slash_xyz_lock.error
@slash_xyz_unlock.error
@slash_xyz_purge.error
@slash_updateranks.error
@slash_updaterules.error
@slash_updatemarket.error
@slash_updatearmory.error
async def admin_command_error(interaction: discord.Interaction, error):
    if isinstance(error, discord.app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Access Denied: Administrator permissions required.", ephemeral=True)

client.run(TOKEN)