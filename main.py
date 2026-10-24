import asyncio
import discord
from discord import app_commands
from discord.ext import tasks, commands
import requests
import json
import os
import time
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load local .env file
load_dotenv()

# ==========================================
# X Y Z SYNDICATE TERMINAL CONFIGURATION
# ==========================================
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", 0))

CHANNELS = {
    "membres": int(os.getenv("CHANNEL_MEMBRES", 0)),      
    "core": int(os.getenv("CHANNEL_CORE", 0)),         
    "apb_status": int(os.getenv("CHANNEL_APB_STATUS", 0)),   
    "quantum": int(os.getenv("CHANNEL_QUANTUM", 0)),      
    "welcome": int(os.getenv("CHANNEL_WELCOME", 0)),      
    "ranks": int(os.getenv("CHANNEL_RANKS", 0)),        
    "rules": int(os.getenv("CHANNEL_RULES", 0)),
    "marketplace": int(os.getenv("CHANNEL_MARKETPLACE", 0)),
    "armory_builds": int(os.getenv("CHANNEL_ARMORY_BUILDS", 0)),
    "citadel_live": int(os.getenv("CHANNEL_CITADEL_LIVE", 0)),
    "apb_news": int(os.getenv("CHANNEL_APB_NEWS", 0)),
    "staff_logs": int(os.getenv("CHANNEL_STAFF_LOGS", 0)),     # Salon verification-logs
    "support": int(os.getenv("CHANNEL_SUPPORT", 0)),           # Salon support-tickets
    "ticket_rules": int(os.getenv("CHANNEL_TICKET_RULES", 0))  # Salon ticket-rules
}

ROLE_IDS = {
    "recruit": int(os.getenv("ROLE_RECRUIT", 0)),      
    "pending": int(os.getenv("ROLE_PENDING", 0)),      
    "denied": int(os.getenv("ROLE_DENIED", 0)),        
    "member": int(os.getenv("ROLE_MEMBER", 0)),
    "guest": int(os.getenv("ROLE_GUEST", 0))          # Rôle Ami / Invité Spécial
}

# ==========================================
# SYNDICATE INDEPENDENT GRADES & ROLES MATRIX (18 TIERS COMPLETS)
# ==========================================
LEVEL_REWARDS = {
    1: {"role_id": int(os.getenv("ROLE_LVL_1", 0)), "name": "⭐・[Lvl 01-04] Outer Fringe Civilian"},
    5: {"role_id": int(os.getenv("ROLE_LVL_5", 0)), "name": "⭐・[Lvl 05] Syndicate Prospect"},
    6: {"role_id": int(os.getenv("ROLE_LVL_6", 0)), "name": "⭐・[Lvl 06-14] Street Runner"},
    15: {"role_id": int(os.getenv("ROLE_LVL_15", 0)), "name": "🛡️・[Lvl 15] Underground Operative"},
    16: {"role_id": int(os.getenv("ROLE_LVL_16", 0)), "name": "🛡️・[Lvl 16-24] Block Operative"},
    25: {"role_id": int(os.getenv("ROLE_LVL_25", 0)), "name": "🛡️・[Lvl 25] Syndicate Specialist"},
    26: {"role_id": int(os.getenv("ROLE_LVL_26", 0)), "name": "🛡️・[Lvl 26-39] District Guardian"},
    40: {"role_id": int(os.getenv("ROLE_LVL_40", 0)), "name": "⚡・[Lvl 40] Sector Vanguard"},
    41: {"role_id": int(os.getenv("ROLE_LVL_41", 0)), "name": "⚡・[Lvl 41-54] Black Market Operative"},
    55: {"role_id": int(os.getenv("ROLE_LVL_55", 0)), "name": "🟠・[Lvl 55] Syndicate Veteran"},
    56: {"role_id": int(os.getenv("ROLE_LVL_56", 0)), "name": "🛡️・[Lvl 56-69] Elite Executioner"},
    70: {"role_id": int(os.getenv("ROLE_LVL_70", 0)), "name": "❌・[Lvl 70] Syndicate Commander"},
    71: {"role_id": int(os.getenv("ROLE_LVL_71", 0)), "name": "❌・[Lvl 71-84] Shadow Strike Lead"},
    85: {"role_id": int(os.getenv("ROLE_LVL_85", 0)), "name": "🔥・[Lvl 85] Mainframe Phantom"},
    86: {"role_id": int(os.getenv("ROLE_LVL_86", 0)), "name": "🔥・[Lvl 86-94] Apex Vanguard"},
    95: {"role_id": int(os.getenv("ROLE_LVL_95", 0)), "name": "💀・[Lvl 95] Syndicate Overlord"},
    96: {"role_id": int(os.getenv("ROLE_LVL_96", 0)), "name": "💀・[Lvl 96-99] Syndicate Prime"},
    100: {"role_id": int(os.getenv("ROLE_LVL_100", 0)), "name": "⚡👑・[Lvl 100] Syndicate Legend"}
}

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True
intents.voice_states = True

# ==========================================
# EXTERNAL APB & LEVELS DATABASE LOADING
# ==========================================
if os.path.exists("apb_database.json"):
    with open("apb_database.json", "r", encoding="utf-8") as f:
        db_data = json.load(f)
        WEAPON_DATABASE = db_data.get("weapons", {})
        SECONDARY_DATABASE = db_data.get("secondaries", {})
        GRENADE_DATABASE = db_data.get("grenades", {})
        MODS_DATABASE = db_data.get("mods", {})
else:
    print("⚠️ [DATABASE ERROR] apb_database.json file not found!")
    WEAPON_DATABASE, SECONDARY_DATABASE, GRENADE_DATABASE, MODS_DATABASE = {}, {}, {}, {}

WEAPON_LIST = list(WEAPON_DATABASE.keys())
SECONDARY_LIST = list(SECONDARY_DATABASE.keys())
GRENADE_LIST = list(GRENADE_DATABASE.keys())
MODS_LIST = list(MODS_DATABASE.keys())

LEVELS_FILE = "levels_database.json"

def load_levels():
    if os.path.exists(LEVELS_FILE):
        try:
            with open(LEVELS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_levels(data):
    with open(LEVELS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ==========================================
# SECURE TICKET SYSTEM (SUPPORT)
# ==========================================

class TicketCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Secure Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket_xyz", emoji="🔒")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 **[MAINFRAME]** Terminating encrypted channel in 5 seconds...", ephemeral=True)
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete(reason=f"Ticket closed by {interaction.user}")
        except Exception as e:
            print(f"⚠️ [TICKET DELETE ERROR]: {e}")

class TicketCreateView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Create Secure Ticket", style=discord.ButtonStyle.success, custom_id="create_ticket_xyz", emoji="🎫")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = interaction.user

        category_name = "🔒 │ ARCHIVES & SUPPORT"
        category = discord.utils.get(guild.categories, name=category_name)

        ticket_channel_name = f"ticket-{member.name}".lower()
        existing_channel = discord.utils.get(guild.text_channels, name=ticket_channel_name)

        if existing_channel:
            await interaction.response.send_message(f"⚠️ You already have an open secure ticket: {existing_channel.mention}", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        }

        staff_role_ids = [ROLE_IDS.get("member", 0)]
        for r_id in staff_role_ids:
            if r_id:
                staff_role = guild.get_role(r_id)
                if staff_role:
                    overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        try:
            ticket_channel = await guild.create_text_channel(
                name=ticket_channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"Secure support ticket for operative {member.name} (ID: {member.id})"
            )
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to create ticket channel: {e}", ephemeral=True)
            return

        embed = discord.Embed(
            title="⚡ X Y Z // SECURE SUPPORT TERMINAL ⚡",
            description=(
                f"> **ENCRYPTED CHANNEL ESTABLISHED**\n"
                f"> *Welcome {member.mention} to your private communication link with the syndicate command.* \n\n"
                f"State the nature of your query, issue, or request clearly. An officer or staff member will connect to this terminal shortly.\n\n"
                f"*Click the button below to close this channel once resolved.*"
            ),
            color=0xD4AF37,
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text="X Y Z Syndicate Support Core • Citadel EU")

        await ticket_channel.send(content=f"🔔 **Secure Link Active:** {member.mention}", embed=embed, view=TicketCloseView())
        await interaction.response.send_message(f"✅ Secure ticket channel generated: {ticket_channel.mention}", ephemeral=True)

# ==========================================
# APPROVAL INTERACTIVE VIEW (VERIFICATION-LOGS)
# ==========================================

class ApprovalView(discord.ui.View):
    def __init__(self, member_id: int, apb_pseudo: str):
        super().__init__(timeout=None)
        self.member_id = member_id
        self.apb_pseudo = apb_pseudo

    @discord.ui.button(label="Approve Operative", style=discord.ButtonStyle.success, custom_id="approve_op_xyz", emoji="✅", row=0)
    async def approve_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = guild.get_member(self.member_id)

        if not member:
            await interaction.response.send_message("❌ Operative no longer found on the server.", ephemeral=True)
            return

        pending_role = guild.get_role(ROLE_IDS["pending"])
        member_role = guild.get_role(ROLE_IDS["member"])

        try:
            if pending_role and pending_role in member.roles:
                await member.remove_roles(pending_role)
            if member_role and member_role not in member.roles:
                await member.add_roles(member_role)
        except Exception as e:
            print(f"⚠️ [APPROVAL ROLE ERROR]: {e}")

        for item in self.children:
            item.disabled = True

        embed = interaction.message.embeds[0]
        embed.color = 0x00FF66
        embed.add_field(name="🛡️ MAINFRAME STATUS", value=f"✅ Approved as Official Member by {interaction.user.mention}", inline=False)

        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message(f"✅ Operative **{self.apb_pseudo}** ({member.mention}) has been successfully approved and granted [Member] clearance.", ephemeral=True)

        data = load_levels()
        current_lvl = data.get(str(member.id), {}).get("level", 1)
        await update_member_nickname_and_role(member, current_lvl, forced_name=self.apb_pseudo)

        try:
            await member.send(f"⚡ **[MAINFRAME CLEARANCE GRANTED]** Your APB callsign **{self.apb_pseudo}** has been verified by the command staff. You are now a fully authorized member of the X Y Z Syndicate!")
        except Exception:
            pass

    @discord.ui.button(label="Approve as Guest", style=discord.ButtonStyle.primary, custom_id="approve_guest_xyz", emoji="🤝", row=0)
    async def guest_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = guild.get_member(self.member_id)

        if not member:
            await interaction.response.send_message("❌ Operative no longer found on the server.", ephemeral=True)
            return

        pending_role = guild.get_role(ROLE_IDS["pending"])
        guest_role = guild.get_role(ROLE_IDS["guest"])

        try:
            if pending_role and pending_role in member.roles:
                await member.remove_roles(pending_role)
            if guest_role and guest_role not in member.roles:
                await member.add_roles(guest_role)
        except Exception as e:
            print(f"⚠️ [GUEST ROLE ERROR]: {e}")

        for item in self.children:
            item.disabled = True

        embed = interaction.message.embeds[0]
        embed.color = 0x00CCFF
        embed.add_field(name="🛡️ MAINFRAME STATUS", value=f"🤝 Approved as Special Guest/Friend by {interaction.user.mention}", inline=False)

        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message(f"🤝 Operative **{self.apb_pseudo}** ({member.mention}) has been approved as a **Special Guest / Friend** of the syndicate.", ephemeral=True)

        data = load_levels()
        current_lvl = data.get(str(member.id), {}).get("level", 1)
        await update_member_nickname_and_role(member, current_lvl, forced_name=self.apb_pseudo)

        try:
            await member.send(f"⚡ **[MAINFRAME GUEST ACCESS]** Your request has been processed. You have been granted special guest clearance to join and play alongside the X Y Z Syndicate operatives!")
        except Exception:
            pass

    @discord.ui.button(label="Reject Callsign", style=discord.ButtonStyle.danger, custom_id="reject_op_xyz", emoji="❌", row=1)
    async def reject_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = guild.get_member(self.member_id)

        pending_role = guild.get_role(ROLE_IDS["pending"])
        denied_role = guild.get_role(ROLE_IDS["denied"])
        recruit_role = guild.get_role(ROLE_IDS["recruit"])

        if member:
            try:
                if pending_role and pending_role in member.roles:
                    await member.remove_roles(pending_role)
                if recruit_role and recruit_role in member.roles:
                    await member.remove_roles(recruit_role)
                if denied_role and denied_role not in member.roles:
                    await member.add_roles(denied_role)
            except Exception as e:
                print(f"⚠️ [REJECT ROLE ERROR]: {e}")

        for item in self.children:
            item.disabled = True

        embed = interaction.message.embeds[0]
        embed.color = 0xFF0000
        embed.add_field(name="🛡️ MAINFRAME STATUS", value=f"❌ Rejected by {interaction.user.mention}", inline=False)

        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message(f"❌ Callsign **{self.apb_pseudo}** rejected. Operative assigned to denied status.", ephemeral=True)

        if member:
            try:
                await member.send(f"⚠️ **[MAINFRAME NOTICE]** Your verification callsign **{self.apb_pseudo}** was not recognized in the X Y Z clan roster. Your access has been restricted.")
            except Exception:
                pass


# ==========================================
# INTERACTIVE ONBOARDING SYSTEMS (VERIFICATION MODAL)
# ==========================================

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
        pending_role = guild.get_role(ROLE_IDS["pending"])

        data = load_levels()
        uid = str(member.id)
        
        if uid not in data:
            data[uid] = {"xp": 0, "level": 1, "messages": 0, "voice_minutes": 0}
            save_levels(data)

        current_lvl = data[uid].get("level", 1)

        clean_name = re.sub(r'(\s*\[Lvl\s+\d+\]\s*)+', '', pseudo).strip()
        formatted_nick = f"{clean_name} [Lvl {current_lvl}]"[:32]

        if member != guild.owner:
            try:
                await member.edit(nick=formatted_nick)
            except Exception as e:
                print(f"⚠️ [VERIFY NICKNAME ERROR]: {e}")

        await update_member_nickname_and_role(member, current_lvl, forced_name=clean_name)

        if recruit_role and recruit_role in member.roles:
            await member.remove_roles(recruit_role)
        if pending_role and pending_role not in member.roles:
            await member.add_roles(pending_role)

        staff_logs_channel = guild.get_channel(CHANNELS.get("staff_logs"))
        if staff_logs_channel:
            approval_embed = discord.Embed(
                title="⚡ PENDING OPERATIVE VERIFICATION ⚡",
                description=(
                    f"> **MAINFRAME SECURITY PENDING**\n\n"
                    f"- **Discord User:** {member.mention} (`{member.name}`)\n"
                    f"- **Provided APB Callsign:** `{clean_name}`\n"
                    f"- **Formatted Nickname:** `{formatted_nick}`\n"
                    f"- **Assigned Level:** `Level {current_lvl}`\n\n"
                    f"*Verify if this operative belongs to the X Y Z clan roster in APB Reloaded, then click a button below.*"
                ),
                color=0xD4AF37,
                timestamp=discord.utils.utcnow()
            )
            approval_embed.set_thumbnail(url=member.display_avatar.url)
            approval_embed.set_footer(text=f"Operative ID: {member.id} • X Y Z Security Core")
            
            await staff_logs_channel.send(
                content=f"🔔 **Staff Verification Required:** New verification request from {member.mention}",
                embed=approval_embed,
                view=ApprovalView(member.id, clean_name)
            )

        await interaction.response.send_message(
            f"✅ **Protocol Submitted!** Callsign registered as **{formatted_nick}**.\n"
            f"⏳ **Pending Approval:** You are placed under review in `verification-logs` while staff checks your presence in the X Y Z clan roster.",
            ephemeral=True
        )

class VerificationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Accept Rules & Set APB Nickname", style=discord.ButtonStyle.success, custom_id="verify_rules_xyz", emoji="⚡")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        member_role = interaction.guild.get_role(ROLE_IDS["member"])
        pending_role = interaction.guild.get_role(ROLE_IDS["pending"])
        
        if member_role and member_role in interaction.user.roles:
            await interaction.response.send_message("⚠️ You have already completed your registration protocol and you are a validated member.", ephemeral=True)
            return
        if pending_role and pending_role in interaction.user.roles:
            await interaction.response.send_message("⏳ Your verification protocol is already pending staff approval in `verification-logs`. Please wait.", ephemeral=True)
            return
            
        await interaction.response.send_modal(VerificationModal())

class RanksOnboardingView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Next: Rules ➡️", style=discord.ButtonStyle.primary, custom_id="ranks_to_rules_xyz", emoji="📜")
    async def next_to_rules(self, interaction: discord.Interaction, button: discord.ui.Button):
        rules_channel = interaction.guild.get_channel(CHANNELS["rules"])
        rules_mention = rules_channel.mention if rules_channel else "#rules"
        
        embed = discord.Embed(
            title="⚡ X Y Z // ONBOARDING: STEP 2 (RULES) ⚡",
            description=(
                f"> **SECURE TRANSMISSION // ACCESS GRANTED**\n"
                f"> *You have reviewed the hierarchy. Now, proceed directly to {rules_mention} above to read our core regulations and validate your final clearance.*\n\n"
                "---\n"
                f"> *« Discipline and mutual respect forge our strength. »*"
            ),
            color=0xD4AF37,
            timestamp=discord.utils.utcnow()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ==========================================
# MODERN ARMORY SYSTEM & BANNER
# ==========================================

class ArmoryNotesModal(discord.ui.Modal, title="X Y Z Syndicate // Tactical Assessment"):
    def __init__(self, interaction_ref: discord.Interaction, weapon: str, max_slots: int, mod1: str, mod2: str, mod3: str, secondary: str, grenade: str):
        super().__init__()
        self.interaction_ref = interaction_ref
        self.weapon = weapon
        self.max_slots = max_slots
        self.mod1 = mod1
        self.mod2 = mod2
        self.mod3 = mod3
        self.secondary = secondary
        self.grenade = grenade

    tactical_notes = discord.ui.TextInput(
        label="Tactical Playstyle & Recoil Assessment",
        placeholder="e.g. Mid-range burst control, optimal mobility, great synergy.",
        style=discord.TextStyle.paragraph,
        min_length=5,
        max_length=300,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        notes = self.tactical_notes.value.strip()
        user = interaction.user

        w_data = WEAPON_DATABASE.get(self.weapon, {"icon": "🔫", "img": None, "type": "Firearm", "max_slots": 3})
        w_img, w_type = w_data["img"], w_data["type"]

        m1_data = MODS_DATABASE.get(self.mod1, {"icon": "⚙️", "color_tag": "Standard"}) if self.mod1 else None
        m2_data = MODS_DATABASE.get(self.mod2, {"icon": "⚙️", "color_tag": "Standard"}) if self.mod2 else None
        m3_data = MODS_DATABASE.get(self.mod3, {"icon": "⚙️", "color_tag": "Standard"}) if self.mod3 else None

        sec_data = SECONDARY_DATABASE.get(self.secondary, {"icon": "🔫", "type": "Secondary"})
        gren_data = GRENADE_DATABASE.get(self.grenade, {"icon": "💥", "type": "Tactical"})

        mods_text = f"🔧 **Slot 01** ➔ `{self.mod1}` *({m1_data['color_tag']})*\n" if self.mod1 else "🔧 **Slot 01** ➔ *[Not Equipped]*\n"
        if self.max_slots >= 2:
            mods_text += f"🔧 **Slot 02** ➔ `{self.mod2}` *({m2_data['color_tag']})*\n" if self.mod2 else "🔧 **Slot 02** ➔ *[Not Equipped]*\n"
        if self.max_slots >= 3:
            mods_text += f"🔧 **Slot 03** ➔ `{self.mod3}` *({m3_data['color_tag']})*\n" if self.mod3 else "🔧 **Slot 03** ➔ *[Not Equipped]*\n"

        embed = discord.Embed(
            title="⚡ X Y Z // SAN PARO ELITE LOADOUT PRESET ⚡",
            description=(
                f"> **MAINFRAME SYNC // SECURE PRESET**\n"
                f"> *Encrypted combat configuration deployed across Citadel EU districts.*\n\n"
                f"### 🎯 **PRIMARY FIREARM SPECIFICATION**\n"
                f"```ini\n"
                f"[ Primary ] : {self.weapon}\n"
                f"[ Class ] : {w_type}\n"
                f"[ Slots ] : {self.max_slots}\n"
                f"```\n"
                f"### ⚙️ **MODIFICATION MATRIX**\n"
                f"{mods_text}\n"
                f"### ⚔️ **SECONDARY & TACTICAL GEAR**\n"
                f"```ini\n"
                f"[ Secondary ] : {self.secondary}\n"
                f"[ Tactical  ] : {self.grenade}\n"
                f"```\n"
                f"### 📝 **TACTICAL & RECOIL ASSESSMENT**\n"
                f"```yaml\n{notes}\n```"
            ),
            color=0xD4AF37,
            timestamp=discord.utils.utcnow()
        )
        
        if w_img and w_img != "https://apbdb.com/images/items/0.png":
            embed.set_thumbnail(url=w_img)
        else:
            embed.set_thumbnail(url=user.display_avatar.url)

        embed.set_image(url="https://cdn.discordapp.com/attachments/1559211818201645066/1559689292933111861/XYZ_Banner_2.png?ex=6acffd59&is=6aceabd9&hm=9bca2268a311a2b9bbcce6194842e8afc1fb1610cec55b521cb990ddb2a78280&")

        embed.set_footer(
            text=f"Designed by {user.name} • X Y Z Syndicate Armory Core", 
            icon_url=user.display_avatar.url
        )

        target_channel = interaction.guild.get_channel(CHANNELS["armory_builds"]) or interaction.channel
        await target_channel.send(content=f"🎯 **New Elite Loadout deployed by** {user.mention}", embed=embed)
        
        await interaction.response.send_message(
            "✅ **Loadout compiled and transmitted!** Your configuration is now live in `🛠️│armory-builds`.",
            ephemeral=True
        )
        
        try:
            await self.interaction_ref.delete_original_response()
        except Exception:
            try:
                await self.interaction_ref.edit_message(content="✅ **Studio session completed and closed.**", embed=None, view=None)
            except Exception:
                pass

class ArmorySecondaryView(discord.ui.View):
    def __init__(self, parent_view):
        super().__init__(timeout=None)
        self.parent = parent_view
        self.update_secondary_components()

    def update_secondary_components(self):
        self.clear_items()

        sec_options = [
            discord.SelectOption(
                label=s, 
                value=s, 
                description=SECONDARY_DATABASE[s]["type"], 
                default=(s == self.parent.selected_secondary)
            ) 
            for s in SECONDARY_LIST
        ]
        sec_select = discord.ui.Select(
            placeholder="🔫 Select Secondary Weapon...", 
            min_values=1, max_values=1, 
            options=sec_options[:25], 
            custom_id="sec_select_xyz", 
            row=0
        )
        sec_select.callback = self.sec_callback
        self.add_item(sec_select)

        gren_options = [
            discord.SelectOption(
                label=g, 
                value=g, 
                description=GRENADE_DATABASE[g]["type"], 
                default=(g == self.parent.selected_grenade)
            ) 
            for g in GRENADE_LIST
        ]
        gren_select = discord.ui.Select(
            placeholder="💥 Select Tactical / Grenade...", 
            min_values=1, max_values=1, 
            options=gren_options[:25], 
            custom_id="gren_select_xyz", 
            row=1
        )
        gren_select.callback = self.gren_callback
        self.add_item(gren_select)

        back_btn = discord.ui.Button(label="⬅️ Back: Primary Weapon", style=discord.ButtonStyle.secondary, custom_id="back_to_primary_btn", row=2)
        back_btn.callback = self.back_callback
        self.add_item(back_btn)

        pub_btn = discord.ui.Button(label="🚀 Publish Complete Loadout", style=discord.ButtonStyle.success, custom_id="publish_loadout_btn", row=2)
        pub_btn.callback = self.pub_callback
        self.add_item(pub_btn)

    async def sec_callback(self, interaction: discord.Interaction):
        self.parent.selected_secondary = interaction.data['values'][0]
        self.update_secondary_components()
        await interaction.response.edit_message(view=self)

    async def gren_callback(self, interaction: discord.Interaction):
        self.parent.selected_grenade = interaction.data['values'][0]
        self.update_secondary_components()
        await interaction.response.edit_message(view=self)

    async def back_callback(self, interaction: discord.Interaction):
        self.parent.update_components()
        await interaction.response.edit_message(embed=self.parent.get_embed_step1(), view=self.parent)

    async def pub_callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ArmoryNotesModal(
            interaction_ref=interaction,
            weapon=self.parent.selected_weapon,
            max_slots=self.parent.max_slots,
            mod1=self.parent.selected_mod1 if self.parent.max_slots > 0 else None, 
            mod2=self.parent.selected_mod2 if self.parent.max_slots >= 2 else None,
            mod3=self.parent.selected_mod3 if self.parent.max_slots >= 3 else None,
            secondary=self.parent.selected_secondary,
            grenade=self.parent.selected_grenade
        ))

class ArmorySelectDropdowns(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
        self.selected_weapon = WEAPON_LIST[0]
        self.max_slots = WEAPON_DATABASE[self.selected_weapon]["max_slots"]
        self.selected_mod1 = None
        self.selected_mod2 = None
        self.selected_mod3 = None
        self.selected_secondary = SECONDARY_LIST[0]
        self.selected_grenade = GRENADE_LIST[0]

        self.update_components()

    def get_embed_step1(self):
        embed = discord.Embed(
            title="🛠️ X Y Z // INTERACTIVE LOADOUT STUDIO (STEP 1)",
            description=(
                f"> **PRIMARY FIREARM & MODIFICATIONS**\n"
                f"> *Selected Weapon:* `{self.selected_weapon}`\n"
                f"> *Allowed Slots:* `{self.max_slots}`\n\n"
                f"Configure your primary weapon below, then click **Next** to select your secondary and tactical gear."
            ),
            color=0xD4AF37
        )
        embed.set_footer(text="X Y Z Syndicate Encryption Protocol • Citadel EU")
        return embed

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
            placeholder="🔫 Select Primary Firearm...",
            min_values=1, max_values=1,
            options=weapon_options[:25],
            custom_id="select_weapon_xyz",
            row=0
        )
        weapon_select.callback = self.weapon_callback
        self.add_item(weapon_select)

        if self.max_slots >= 1:
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
        else:
            self.selected_mod1 = None

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

        next_button = discord.ui.Button(
            label="Next: Secondary & Gear ➡️", 
            style=discord.ButtonStyle.primary, 
            custom_id="next_to_sec_btn", 
            emoji="⚙️", 
            row=4
        )
        next_button.callback = self.next_callback
        self.add_item(next_button)

    async def weapon_callback(self, interaction: discord.Interaction):
        self.selected_weapon = interaction.data['values'][0]
        self.update_components()
        await interaction.response.edit_message(embed=self.get_embed_step1(), view=self)

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

    async def next_callback(self, interaction: discord.Interaction):
        if self.max_slots >= 1 and not self.selected_mod1:
            await interaction.response.send_message(f"❌ **Error:** This firearm allows {self.max_slots} slots. Please equip Slot 1.", ephemeral=True)
            return
        if self.max_slots >= 2 and not self.selected_mod2:
            await interaction.response.send_message(f"❌ **Error:** This firearm allows {self.max_slots} slots. Please equip Slot 2.", ephemeral=True)
            return
        if self.max_slots >= 3 and not self.selected_mod3:
            await interaction.response.send_message(f"❌ **Error:** This firearm allows {self.max_slots} slots. Please equip Slot 3.", ephemeral=True)
            return

        embed_step2 = discord.Embed(
            title="🛠️ X Y Z // INTERACTIVE LOADOUT STUDIO (STEP 2)",
            description=(
                f"> **SECONDARY WEAPON & TACTICAL GEAR**\n"
                f"> *Primary:* `{self.selected_weapon}`\n\n"
                f"Select your secondary firearm and tactical grenade below, then click **Publish**."
            ),
            color=0xD4AF37
        )
        embed_step2.set_footer(text="X Y Z Syndicate Encryption Protocol • Citadel EU")
        
        await interaction.response.edit_message(embed=embed_step2, view=ArmorySecondaryView(self))

class ArmoryView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Initialize Loadout Studio Terminal", style=discord.ButtonStyle.primary, custom_id="open_armory_studio_xyz", emoji="🛠️")
    async def open_studio(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = ArmorySelectDropdowns()
        await interaction.response.send_message(embed=view.get_embed_step1(), view=view, ephemeral=True)

# ==========================================
# MARKETPLACE
# ==========================================
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

# ==========================================
# MAIN BOT CONFIGURATION
# ==========================================
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
        self.add_view(TicketCreateView())
        self.add_view(TicketCloseView())
        print("⚡ [DISCORD] Slash commands and persistent views synchronized.")

client = XYZBot()

# ==========================================
# TACTICAL STATUS ROTATION
# ==========================================
@tasks.loop(seconds=20)
async def rotate_bot_presence():
    statuses = [
        discord.Game(name="APB Reloaded // Citadel EU ⚡"),
        discord.Activity(type=discord.ActivityType.watching, name="San Paro Streets & Districts 🏙️"),
        discord.Activity(type=discord.ActivityType.listening, name="Syndicate Secure Radio 📡"),
        discord.Game(name="X Y Z Syndicate Core 💀"),
        discord.Activity(type=discord.ActivityType.playing, name="Financial & Waterfront Warfare 🎯"),
        discord.Activity(type=discord.ActivityType.watching, name="Over Crimson & Enforcer Targets 🏎️"),
        discord.Game(name="Marketplace & Armory Matrix 💼"),
        discord.Activity(type=discord.ActivityType.listening, name="Elite Operatives Comms 🎧")
    ]
    for status in statuses:
        await client.change_presence(status=discord.Status.online, activity=status)
        await asyncio.sleep(20)

@rotate_bot_presence.before_loop
async def before_rotate():
    await client.wait_until_ready()

# ==========================================
# APB CITADEL (EU) SCRAPER EXCLUSIF EUROPE (PRÉCIS & CALCULS PARFAITS)
# ==========================================
def fetch_citadel_detailed_status():
    data = {
        "status": "Online 🟢",
        "total_ccu": 0,
        "enf_total": 0,
        "crim_total": 0,
        "districts": []
    }
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.9"
        }
        res = requests.get("https://www.gamersfirst.com/apb/status", headers=headers, timeout=8.0)
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # On cible uniquement le conteneur européen officiel id="panel-EU"
            eu_panel = soup.find(id="panel-EU")
            if not eu_panel:
                eu_panel = soup # Fallback si l'ID change
            
            # Extraction des totaux globaux de la section Europe
            sum_total_elem = eu_panel.find(class_='sum-total')
            if sum_total_elem:
                match_online = re.search(r'(\d+)', sum_total_elem.get_text())
                if match_online:
                    data["total_ccu"] = int(match_online.group(1))

            enf_summary = eu_panel.find('span', class_='enf')
            crim_summary = eu_panel.find('span', class_='crim')
            
            if enf_summary:
                match_enf = re.search(r'(\d+)', enf_summary.get_text())
                if match_enf:
                    data["enf_total"] = int(match_enf.group(1))
                    
            if crim_summary:
                match_crim = re.search(r'(\d+)', crim_summary.get_text())
                if match_crim:
                    data["crim_total"] = int(match_crim.group(1))

            parsed_districts = []
            
            # Récupération de chaque ligne de district dans le tableau européen
            district_rows = eu_panel.find_all(class_='status-district')
            
            calc_online = 0
            calc_enf = 0
            calc_crim = 0

            for row in district_rows:
                # Nom du district
                name_elem = row.find(class_='d-name')
                if not name_elem:
                    continue
                clean_name = name_elem.get_text().strip()
                
                # Type de district (Missions, Social, Fight Club, Dynamic Event, Community Event)
                type_elem = row.find(class_='d-type')
                d_type = type_elem.get_text().strip().upper() if type_elem else "MISSIONS"

                # Population totale du district
                pop_elem = row.find(class_='d-total')
                pop_val = int(pop_elem.get_text().strip()) if pop_elem and pop_elem.get_text().strip().isdigit() else 0

                # Récupération exacte des Enforcers et Criminals via l'attribut title de cell-c (ex: title="27 ENF · 30 CRIM")
                enf_val = 0
                crim_val = 0
                cell_c = row.find(class_='cell-c')
                if cell_c and cell_c.has_attr('title'):
                    title_text = cell_c['title']
                    m_enf = re.search(r'(\d+)\s*ENF', title_text)
                    m_crim = re.search(r'(\d+)\s*CRIM', title_text)
                    if m_enf:
                        enf_val = int(m_enf.group(1))
                    if m_crim:
                        crim_val = int(m_crim.group(1))
                
                # Sécurité de secours si le title n'est pas trouvé : lecture des barres flex CSS
                if enf_val == 0 and crim_val == 0 and pop_val > 0:
                    enf_span = row.find('span', class_='enf', style=True)
                    crim_span = row.find('span', class_='crim', style=True)
                    flex_enf = float(re.search(r'flex:\s*([\d.]+)', enf_span.get('style', '')).group(1)) if enf_span else 1.0
                    flex_crim = float(re.search(r'flex:\s*([\d.]+)', crim_span.get('style', '')).group(1)) if crim_span else 1.0
                    total_flex = flex_enf + flex_crim
                    enf_val = round(pop_val * (flex_enf / total_flex))
                    crim_val = pop_val - enf_val

                calc_online += pop_val
                calc_enf += enf_val
                calc_crim += crim_val

                parsed_districts.append({
                    "name": clean_name,
                    "type": d_type,
                    "pop": pop_val,
                    "enf": enf_val,
                    "crim": crim_val
                })

            if parsed_districts:
                # Tri dynamique du plus actif au plus calme
                parsed_districts = sorted(parsed_districts, key=lambda x: x['pop'], reverse=True)
                data["districts"] = parsed_districts
                
                # Synchronisation parfaite des totaux globaux avec la somme réelle des districts EU
                if calc_online > 0:
                    data["total_ccu"] = calc_online
                if calc_enf > 0:
                    data["enf_total"] = calc_enf
                if calc_crim > 0:
                    data["crim_total"] = calc_crim

        # Sauvegarde propre dans citadel_data.json
        with open("citadel_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    except Exception as e:
        print(f"⚠️ [CITADEL SCRAPER ERROR]: {e}")
        if os.path.exists("citadel_data.json"):
            with open("citadel_data.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                
    return data

# ==========================================
# APB NEWS SCRAPER (LATEST 10 POSTS)
# ==========================================
def fetch_apb_news():
    news_list = []
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        res = requests.get("https://www.gamersfirst.com/apb/news", headers=headers, timeout=5.0)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            links = soup.find_all('a', href=re.compile(r'/apb/news/\d{4}/'))
            seen_links = set()
            
            for link in links:
                href = link.get('href', '')
                if href and href not in seen_links:
                    seen_links.add(href)
                    if not href.startswith('http'):
                        href = "https://www.gamersfirst.com" + href
                    
                    title = link.get_text().strip()
                    if len(title) > 5:
                        news_list.append({
                            "title": title,
                            "url": href,
                            "date": "Official Dispatch"
                        })
                if len(news_list) >= 10:
                    break
                    
            if not news_list:
                news_list = [
                    {"title": "Halloween 2026: Apocalypse", "url": "https://www.gamersfirst.com/apb/news/2026/10/14/halloween-2026-apocalypse", "date": "October 14, 2026 | PC"},
                    {"title": "APB 1.33 Loud and Clear", "url": "https://www.gamersfirst.com/apb/news/", "date": "September 15, 2026 | PC"},
                    {"title": "Summer Nights 2026", "url": "https://www.gamersfirst.com/apb/news/", "date": "August 22, 2026 | PC"},
                    {"title": "Mega AMA with Matt Scott", "url": "https://www.gamersfirst.com/apb/news/", "date": "August 6, 2026 | PC"},
                    {"title": "Power Week 2026", "url": "https://www.gamersfirst.com/apb/news/", "date": "July 23, 2026 | PC"},
                    {"title": "Heatwave 2026", "url": "https://www.gamersfirst.com/apb/news/", "date": "June 18, 2026 | PC"},
                    {"title": "The Legends Update: New Contacts & Weapons", "url": "https://www.gamersfirst.com/apb/news/", "date": "March 27, 2026 | PC"},
                    {"title": "Spring Event Returns to San Paro", "url": "https://www.gamersfirst.com/apb/news/", "date": "March 28, 2026 | PC"},
                    {"title": "Introducing The Vault System", "url": "https://www.gamersfirst.com/apb/news/", "date": "December 18, 2025 | PC"},
                    {"title": "Epidemic Returns: Halloween 2025", "url": "https://www.gamersfirst.com/apb/news/", "date": "October 15, 2025 | PC"}
                ]
    except Exception as e:
        print(f"⚠️ [NEWS SCRAPER ERROR]: {e}")
        news_list = []
        
    return news_list[:10]

# ==========================================
# X Y Z LEVELING & RIGHT-SIDE PSEUDO SYNC (CONSERVE LE PSEUDO APB)
# ==========================================
XP_COOLDOWN = {}

async def update_member_nickname_and_role(member: discord.Member, new_level: int, forced_name: str = None):
    guild = member.guild
    
    if member == guild.owner:
        return

    if forced_name:
        clean_name = re.sub(r'(\s*\[Lvl\s+\d+\]\s*)+', '', forced_name).strip()
    else:
        current_nick = member.nick or member.name
        clean_name = re.sub(r'(\s*\[Lvl\s+\d+\]\s*)+', '', current_nick).strip()

    new_nick = f"{clean_name} [Lvl {new_level}]"[:32]

    if member.nick != new_nick:
        try:
            await member.edit(nick=new_nick)
        except Exception as e:
            print(f"⚠️ [NICKNAME UPDATE ERROR]: {e}")

    sorted_tiers = sorted(LEVEL_REWARDS.items(), key=lambda x: x[0], reverse=True)
    
    assigned_role_id = None
    for lvl_threshold, info in sorted_tiers:
        if new_level >= lvl_threshold:
            assigned_role_id = info["role_id"]
            break

    for lvl_threshold, info in LEVEL_REWARDS.items():
        role_id = info["role_id"]
        if not role_id:
            continue
        role = guild.get_role(role_id)
        if not role:
            continue

        if role_id == assigned_role_id:
            if role not in member.roles:
                try:
                    await member.add_roles(role)
                except Exception as e:
                    print(f"⚠️ [ROLE ADD ERROR]: {e}")
        else:
            if role in member.roles:
                try:
                    await member.remove_roles(role)
                except Exception as e:
                    print(f"⚠️ [ROLE REMOVE ERROR]: {e}")

def add_xp_to_user(user_id: str, guild: discord.Guild, xp_amount: int, is_message: bool = False, is_voice: bool = False):
    data = load_levels()
    if user_id not in data:
        data[user_id] = {"xp": 0, "level": 1, "messages": 0, "voice_minutes": 0}

    if is_message:
        data[user_id]["messages"] += 1
    if is_voice:
        data[user_id]["voice_minutes"] += 1

    current_level = data[user_id]["level"]
    if current_level >= 100:
        data[user_id]["level"] = 100
        data[user_id]["xp"] = 0
        save_levels(data)
        return 100, False

    data[user_id]["xp"] += xp_amount
    current_xp = data[user_id]["xp"]
    xp_needed = current_level * 350
    leveled_up = False

    if current_xp >= xp_needed and current_level < 100:
        data[user_id]["level"] += 1
        data[user_id]["xp"] = current_xp - xp_needed
        leveled_up = True

    save_levels(data)
    return data[user_id]["level"], leveled_up

@tasks.loop(minutes=1)
async def voice_xp_tracker():
    guild = client.get_guild(GUILD_ID)
    if not guild:
        return

    afk_channel = guild.afk_channel

    for vc in guild.voice_channels:
        if afk_channel and vc.id == afk_channel.id:
            continue
        for member in vc.members:
            if member.bot:
                continue
            if member.voice and (member.voice.self_mute or member.voice.self_deaf):
                continue

            uid = str(member.id)
            lvl, leveled = add_xp_to_user(uid, guild, 12, is_voice=True)
            await update_member_nickname_and_role(member, lvl)
            if leveled:
                try:
                    await member.send(f"⚡ **[MAINFRAME LEVEL UP]** Congratulations operative `{member.name}`! Your vocal tactical sync has elevated you to **Level {lvl}**.")
                except Exception:
                    pass

@client.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        await client.process_commands(message)
        return

    uid = str(message.author.id)
    now = time.time()

    if uid in XP_COOLDOWN and now - XP_COOLDOWN[uid] < 45:
        await client.process_commands(message)
        return

    XP_COOLDOWN[uid] = now
    import random
    earned_xp = random.randint(20, 35)
    
    lvl, leveled = add_xp_to_user(uid, message.guild, earned_xp, is_message=True)
    await update_member_nickname_and_role(message.author, lvl)

    if leveled:
        try:
            await message.channel.send(f"⚡ **[MAINFRAME LEVEL UP]** {message.author.mention} has achieved tactical clearance **Level {lvl}**! Keep dominating San Paro.")
        except Exception:
            pass

    await client.process_commands(message)

# ==========================================
# ADMIN SYNCHRONIZATION COMMANDS
# ==========================================

@client.tree.command(name="sync-all", description="[ADMIN] Finds members without [Lvl] tag, assigns their level badge, and syncs roles.")
@app_commands.checks.has_permissions(administrator=True)
async def slash_sync_all(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    data = load_levels()
    
    updated_count = 0
    scanned_count = 0

    for member in guild.members:
        if member.bot or member == guild.owner:
            continue

        scanned_count += 1
        uid = str(member.id)
        
        user_info = data.get(uid, {"level": 1})
        lvl = user_info.get("level", 1)

        await update_member_nickname_and_role(member, lvl)
        updated_count += 1

    await interaction.followup.send(
        f"✅ **Mainframe Scan Complete!**\n"
        f"- Scanned: `{scanned_count}` operatives\n"
        f"- Synchronized nicknames and level roles for **{updated_count}** operatives.",
        ephemeral=True
    )

@client.tree.command(name="sync-name", description="Forces synchronization of your level badge [Lvl XX] on your profile.")
async def slash_sync_name(interaction: discord.Interaction):
    member = interaction.user
    guild = interaction.guild
    
    if member == guild.owner:
        await interaction.response.send_message("⚠️ As server owner, Discord restricts bots from modifying your nickname automatically. Your level is fully tracked via `/rank`!", ephemeral=True)
        return

    data = load_levels()
    uid = str(member.id)
    lvl = data.get(uid, {}).get("level", 1)
    
    await update_member_nickname_and_role(member, lvl)
    await interaction.response.send_message(f"✅ Callsign and level role synchronized with **Level {lvl}**!", ephemeral=True)


@client.tree.command(name="rank", description="Displays your current operative level (1-100), progression and statistics.")
@app_commands.describe(member="The operative you want to inspect (leave blank for yourself)")
async def slash_rank(interaction: discord.Interaction, member: discord.Member = None):
    target = member or interaction.user
    uid = str(target.id)
    data = load_levels()

    if uid not in data:
        user_data = {"xp": 0, "level": 1, "messages": 0, "voice_minutes": 0}
    else:
        user_data = data[uid]

    lvl = user_data["level"]
    xp = user_data["xp"]
    needed = lvl * 350
    msgs = user_data["messages"]
    v_mins = user_data["voice_minutes"]

    progress = int((xp / needed) * 10) if needed > 0 else 10
    bar = "▰" * min(progress, 10) + "▱" * (10 - min(progress, 10))

    embed = discord.Embed(
        title=f"⚡ X Y Z // OPERATIVE DOSSIER: {target.name} ⚡",
        description=(
            f"> **MAINFRAME SECURITY CLEARANCE**\n\n"
            f"```ini\n"
            f"[ OPERATIVE  ] : {target.name}\n"
            f"[ LEVEL (1-100)] : Level {lvl} / 100\n"
            f"[ PROGRESS   ] : [{bar}] {int((xp/needed)*100 if needed > 0 else 100)}%\n"
            f"[ CURRENT XP ] : {xp} / {needed} XP\n"
            f"[ CHAT MSGS  ] : {msgs} transmissions\n"
            f"[ VOICE TIME ] : {v_mins} minutes active\n"
            f"```"
        ),
        color=0xD4AF37,
        timestamp=discord.utils.utcnow()
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.set_footer(text="X Y Z Syndicate Personnel Database • Citadel EU", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
    
    await interaction.response.send_message(embed=embed, ephemeral=False)

@client.tree.command(name="leaderboard", description="Displays the top 10 most active operatives based on levels and XP.")
async def slash_leaderboard(interaction: discord.Interaction):
    data = load_levels()
    if not data:
        await interaction.response.send_message("⚠️ No telemetry data recorded in the mainframe yet.", ephemeral=True)
        return

    sorted_users = sorted(data.items(), key=lambda x: (x[1]["level"], x[1]["xp"]), reverse=True)[:10]

    lb_text = ""
    for idx, (uid, info) in enumerate(sorted_users, start=1):
        member = interaction.guild.get_member(int(uid))
        if member:
            current_nick = member.nick or member.name
            apb_name = re.sub(r'(\s*\[Lvl\s+\d+\]\s*)+', '', current_nick).strip()
        else:
            apb_name = f"Operative #{uid}"

        lvl = info["level"]
        medal = "👑" if idx == 1 else ("🥈" if idx == 2 else ("🥉" if idx == 3 else f"`#{idx}`"))
        lb_text += f"{medal} **{apb_name}** ➔ **Level {lvl} / 100** *({info['xp']} XP)* | 💬 `{info['messages']}` msgs\n"

    embed = discord.Embed(
        title="⚡ X Y Z // ELITE OPERATIVES LEADERBOARD ⚡",
        description=(
            f"> **MAINFRAME TOP 10 RANKING**\n"
            f"> *Most active combatants across chat and voice channels in San Paro.*\n\n"
            f"{lb_text}"
        ),
        color=0xD4AF37,
        timestamp=discord.utils.utcnow()
    )
    embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
    embed.set_footer(text="X Y Z Syndicate Leaderboard Core • Citadel EU")

    await interaction.response.send_message(embed=embed)

@client.tree.command(name="rewards", description="Displays independent syndicate grades unlocked at specific level milestones.")
async def slash_rewards(interaction: discord.Interaction):
    rewards_text = ""
    for lvl, info in LEVEL_REWARDS.items():
        role = interaction.guild.get_role(info["role_id"])
        role_mention = role.mention if role else f"Role ID: {info['role_id']}"
        rewards_text += f"🎯 **Level {lvl:3} Milestone** ➔ **{info['name']}** ({role_mention})\n"

    if not rewards_text:
        rewards_text = "⚠️ No independent role rewards configured in the mainframe yet."

    embed = discord.Embed(
        title="⚡ X Y Z // INDEPENDENT GRADES & MILESTONES ⚡",
        description=(
            f"> **MAINFRAME PROMOTION MATRIX**\n"
            f"> *Reach specific levels (1-100) to unlock prestigious syndicate combat roles independently.*\n\n"
            f"{rewards_text}"
        ),
        color=0xD4AF37,
        timestamp=discord.utils.utcnow()
    )
    embed.set_footer(text="X Y Z Syndicate Progression Core")
    await interaction.response.send_message(embed=embed)


@tasks.loop(minutes=2)
async def auto_update_citadel_live():
    guild = client.get_guild(GUILD_ID)
    if not guild:
        return
        
    target_channel_id = CHANNELS.get("citadel_live")
    target_channel = guild.get_channel(target_channel_id)
    if not target_channel:
        return

    api_data = await asyncio.to_thread(fetch_citadel_detailed_status)
    
    districts_text = ""
    for d in api_data["districts"]:
        clean_name = re.sub(r'\s*\(#?\d+\)', '', d['name'])
        clean_name = re.sub(r'#\d+', '', clean_name).strip()
        icon = "🏙️" if "Financial" in clean_name else ("🌊" if "Waterfront" in clean_name else ("☕" if "Social" in clean_name else ("🥊" if "Fight" in clean_name else "⚡")))
        
        pop = d['pop']
        enf = d['enf']
        crim = d['crim']
        districts_text += f"> {icon} **`{clean_name:<28}`** ➔ `{d['type']:<15}` | 👥 **{pop}p** (🛡️ `{enf}` | 💀 `{crim}`)\n"

    total = api_data['total_ccu']
    enf_tot = api_data['enf_total']
    crim_tot = api_data['crim_total']
    
    enf_pct = int((enf_tot / total) * 100) if total > 0 else 0
    crim_pct = int((crim_tot / total) * 100) if total > 0 else 0

    bar_length = 10
    enf_blocks = int((enf_tot / total) * bar_length) if total > 0 else 5
    crim_blocks = bar_length - enf_blocks
    progress_bar = "🟦" * enf_blocks + "🟥" * crim_blocks

    embed = discord.Embed(
        title="⚡ SAN PARO // CITADEL (EU) LIVE DISTRICTS ⚡",
        description=(
            f"> **MAINFRAME LIVE TELEMETRY**\n"
            f"> *Real-time tactical intelligence intercepted across San Paro servers.*\n\n"
            f"```ini\n"
            f"[ SYSTEM STATUS ] : {api_data['status']}\n"
            f"[ TOTAL ONLINE  ] : {total} PLAYERS\n"
            f"[ ENFORCERS     ] : {enf_tot} UNITS ({enf_pct}%) 🛡️\n"
            f"[ CRIMINALS     ] : {crim_tot} UNITS ({crim_pct}%) 💀\n"
            f"```\n"
            f"**GLOBAL RATIO:** {progress_bar}\n"
            f"---\n"
            f"### 🏙️ **COMPLETE DISTRICT MATRIX**\n"
            f"{districts_text}"
        ),
        color=0xD4AF37,
        timestamp=discord.utils.utcnow()
    )
    
    embed.set_thumbnail(url="https://apbdb.com/images/items/0.png")
    embed.set_image(url="https://cdn.discordapp.com/attachments/1559211818201645066/1560289839688196206/XYZ_Banner_4.png?ex=6ad22ca6&is=6ad0db26&hm=58c9e62cf921d18757785adc97caa48f6a7a312ac93daf03ba9dc514c08cb391&")
    embed.set_footer(text="GamersFirst Web Scraper • X Y Z Syndicate Core", icon_url=guild.icon.url if guild.icon else None)

    try:
        async for message in target_channel.history(limit=10):
            if message.author == client.user or message.author == guild.me:
                await message.edit(embed=embed)
                return
        await target_channel.send(embed=embed)
    except Exception as e:
        print(f"⚠️ [CITADEL LIVE ERROR]: {e}")

@auto_update_citadel_live.before_loop
async def before_citadel_live():
    await client.wait_until_ready()

@client.event
async def on_ready():
    print(f"🤖 X Y Z Syndicate Bot connected and operational as {client.user}!")
    
    with open("core_status.json", "w") as f:
        json.dump({"status": "Online"}, f)
        
    if not update_cluster_stats.is_running():
        update_cluster_stats.start()
        
    if not rotate_bot_presence.is_running():
        rotate_bot_presence.start()

    if not auto_update_citadel_live.is_running():
        auto_update_citadel_live.start()

    if not voice_xp_tracker.is_running():
        voice_xp_tracker.start()

@client.event
async def on_member_join(member: discord.Member):
    if member.guild.id != GUILD_ID:
        return

    recruit_role = member.guild.get_role(ROLE_IDS["recruit"])
    if recruit_role:
        try:
            await member.add_roles(recruit_role)
        except Exception as e:
            print(f"⚠️ [ROLE ERROR] Could not assign recruit role: {e}")

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
                f"\u001b[2;33m[STATUS] ➔ Assigned Rank: [Recruit]\u001b[0m\n"
                f"\u001b[2;33m[TARGET] ➔ Complete Onboarding & Verification\u001b[0m\n"
                f"```\n\n"
                f"A secure direct briefing has been transmitted to your private terminal. Follow the instructions to claim your operational status."
            ),
            color=0xD4AF37,
            timestamp=discord.utils.utcnow()
        )
        embed_public.set_thumbnail(url=member.display_avatar.url)
        embed_public.set_image(url="https://cdn.discordapp.com/attachments/1559211818201645066/1560058116912062506/XYZ_Banner_3.png?ex=6ad154d7&is=6ad00357&hm=d6e14419ced78098f060af8e2460b6248f5353e2654991143510756f6a4feb90&")
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
        embed_dm.set_thumbnail(url=member.display_avatar.url)
        embed_dm.set_image(url="https://cdn.discordapp.com/attachments/1559211818201645066/1559689292933111861/XYZ_Banner_2.png?ex=6acffd59&is=6aceabd9&hm=9bca2268a311a2b9bbcce6194842e8afc1fb1610cec55b521cb990ddb2a78280&")
        embed_dm.set_footer(text="X Y Z Syndicate Security Core")
        await member.send(embed=embed_dm)
    except discord.Forbidden:
        print(f"⚠️ [DM ERROR] Could not send private message to {member.name}.")

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

@tasks.loop(minutes=15)
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
        if key in ["welcome", "ranks", "rules", "marketplace", "armory_builds", "citadel_live", "apb_news", "staff_logs", "support", "ticket_rules"]:
            continue
        channel = guild.get_channel(channel_id)
        if channel and channel.name != new_names[key]:
            try:
                await channel.edit(name=new_names[key])
                await asyncio.sleep(1)
            except discord.HTTPException as e:
                print(f"⚠️ [DISCORD] Rate Limit or Error on {key}: {e}")
            except Exception as e:
                print(f"❌ [DISCORD] Channel error {key}: {e}")

@update_cluster_stats.before_loop
async def before_update():
    await client.wait_until_ready()

# ==========================================
# CLAN & MANAGEMENT COMMANDS
# ==========================================

@client.tree.command(name="apb-news", description="[ADMIN] Publishes the 10 latest official APB Reloaded news & updates.")
@app_commands.checks.has_permissions(administrator=True)
async def slash_apb_news(interaction: discord.Interaction):
    target_channel_id = CHANNELS.get("apb_news")
    target_channel = interaction.guild.get_channel(target_channel_id)

    if not target_channel:
        await interaction.response.send_message(
            f"❌ **Configuration Error:** Channel `apb-news` not found in .env file.",
            ephemeral=True
        )
        return

    await interaction.response.send_message("📡 Intercepting official APB Reloaded intelligence feeds...", ephemeral=True)

    news_items = await asyncio.to_thread(fetch_apb_news)
    
    if not news_items:
        await interaction.followup.send("❌ Could not retrieve news feed from GamersFirst.", ephemeral=True)
        return

    news_unique_banner = "https://cdn.discordapp.com/attachments/1559211818201645066/1560289839688196206/XYZ_Banner_4.png?ex=6ad22ca6&is=6ad0db26&hm=58c9e62cf921d18757785adc97caa48f6a7a312ac93daf03ba9dc514c08cb391&"

    header_embed = discord.Embed(
        title="⚡ X Y Z // SAN PARO OFFICIAL NEWS ARCHIVES ⚡",
        description=(
            f"> **SECURE MAINFRAME FEED // LATEST 10 UPDATES**\n"
            f"> *Intercepted patches, developer announcements, and seasonal updates from GamersFirst.*"
        ),
        color=0xD4AF37,
        timestamp=discord.utils.utcnow()
    )
    header_embed.set_image(url=news_unique_banner)
    header_embed.set_footer(text="X Y Z Syndicate Intelligence Core", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
    
    await target_channel.send(embed=header_embed)

    for idx, item in enumerate(news_items, start=1):
        news_embed = discord.Embed(
            title=f"📰 [{idx}/10] {item['title']}",
            description=(
                f"```ini\n"
                f"[ SOURCE   ] : GamersFirst Official Network\n"
                f"[ DATE     ] : {item['date']}\n"
                f"[ STATUS   ] : Archived & Verified 🟢\n"
                f"```\n"
                f"🔗 **[Access Official Dispatch]({item['url']})**"
            ),
            color=0x00CCFF,
            timestamp=discord.utils.utcnow()
        )
        news_embed.set_thumbnail(url="https://apbdb.com/images/items/0.png")
        news_embed.set_footer(text=f"X Y Z Syndicate News Matrix • Post ID: {idx}")
        
        await target_channel.send(embed=news_embed)
        await asyncio.sleep(0.5)

@client.tree.command(name="apb-citadel", description="[ADMIN] Publishes or forces manual refresh of Citadel live telemetry.")
@app_commands.checks.has_permissions(administrator=True)
async def slash_apb_citadel(interaction: discord.Interaction):
    target_channel_id = CHANNELS.get("citadel_live")
    target_channel = interaction.guild.get_channel(target_channel_id)

    if not target_channel:
        await interaction.response.send_message(
            f"❌ **Configuration Error:** Channel `citadel-live` not found in .env file.",
            ephemeral=True
        )
        return

    await interaction.response.send_message("📡 Manual refresh of Citadel live telemetry triggered...", ephemeral=True)

    api_data = await asyncio.to_thread(fetch_citadel_detailed_status)
    
    districts_text = ""
    for d in api_data["districts"]:
        clean_name = re.sub(r'\s*\(#?\d+\)', '', d['name'])
        clean_name = re.sub(r'#\d+', '', clean_name).strip()
        icon = "🏙️" if "Financial" in clean_name else ("🌊" if "Waterfront" in clean_name else ("☕" if "Social" in clean_name else ("🥊" if "Fight" in clean_name else "⚡")))
        
        pop = d['pop']
        enf = d['enf']
        crim = d['crim']
        districts_text += f"> {icon} **`{clean_name:<28}`** ➔ `{d['type']:<15}` | 👥 **{pop}p** (🛡️ `{enf}` | 💀 `{crim}`)\n"

    total = api_data['total_ccu']
    enf_tot = api_data['enf_total']
    crim_tot = api_data['crim_total']
    
    enf_pct = int((enf_tot / total) * 100) if total > 0 else 0
    crim_pct = int((crim_tot / total) * 100) if total > 0 else 0

    embed = discord.Embed(
        title="⚡ SAN PARO // CITADEL (EU) LIVE DISTRICTS ⚡",
        description=(
            f"> **MAINFRAME LIVE TELEMETRY**\n"
            f"> *Real-time tactical intelligence intercepted across San Paro servers.*\n\n"
            f"```ini\n"
            f"[ SYSTEM STATUS ] : {api_data['status']}\n"
            f"[ TOTAL ONLINE  ] : {total} PLAYERS\n"
            f"[ ENFORCERS     ] : {enf_tot} UNITS ({enf_pct}%) 🛡️\n"
            f"[ CRIMINALS     ] : {crim_tot} UNITS ({crim_pct}%) 💀\n"
            f"```\n"
            f"---\n"
            f"### 🏙️ **COMPLETE DISTRICT MATRIX**\n"
            f"{districts_text}"
        ),
        color=0xD4AF37,
        timestamp=discord.utils.utcnow()
    )
    
    embed.set_thumbnail(url="https://apbdb.com/images/items/0.png")
    embed.set_image(url="https://cdn.discordapp.com/attachments/1559211818201645066/1560289839688196206/XYZ_Banner_4.png?ex=6ad22ca6&is=6ad0db26&hm=58c9e62cf921d18757785adc97caa48f6a7a312ac93daf03ba9dc514c08cb391&")
    embed.set_footer(text="GamersFirst Web Scraper • X Y Z Syndicate Core", icon_url=guild.icon.url if guild.icon else None)
    
    try:
        async for message in target_channel.history(limit=10):
            if message.author == client.user or message.author == guild.me:
                await message.edit(embed=embed)
                return
        await target_channel.send(embed=embed)
    except Exception as e:
        print(f"⚠️ [APBD-CITADEL CMD ERROR]: {e}")

@client.tree.command(name="xyz-poll", description="[OFFICER] Launches an official tactical poll.")
@app_commands.describe(question="The question or objective for the operatives")
@app_commands.checks.has_permissions(administrator=True)
async def slash_xyz_poll(interaction: discord.Interaction, question: str):
    embed = discord.Embed(
        title="⚡ X Y Z // SYNDICATE TACTICAL POLL ⚡",
        description=f"> **OBJECTIVE / QUERY:**\n> *{question}*\n\nReact below to cast your operational vote.",
        color=0xD4AF37,
        timestamp=discord.utils.utcnow()
    )
    embed.set_footer(text=f"Poll initiated by {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
    
    await interaction.response.send_message("✅ Tactical poll successfully broadcasted.", ephemeral=True)
    msg = await interaction.channel.send(content="📊 **NEW OPERATIONAL POLL:**", embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

@client.tree.command(name="xyz-membercount", description="Displays detailed statistics of syndicate operatives.")
async def slash_xyz_membercount(interaction: discord.Interaction):
    guild = interaction.guild
    total = guild.member_count
    
    embed = discord.Embed(
        title="⚡ X Y Z // ROSTER TELEMETRY",
        description=(
            f"> **MAINFRAME STATUS // SYNCHRONIZED**\n\n"
            f"- **Total Operatives Connected:** `{total:,}`\n"
            f"- **District Base:** Citadel (EU)\n"
            f"- **Syndicate Status:** Fully Operational 🟢"
        ),
        color=0xD4AF37,
        timestamp=discord.utils.utcnow()
    )
    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@client.tree.command(name="xyz-rules", description="Displays quick security directives.")
async def slash_xyz_rules(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚡ X Y Z // CORE PROTOCOLS SUMMARY",
        description=(
            "> **01.** Mutual respect is mandatory. Toxic behavior leads to immediate blacklisting.\n"
            "> **02.** Operatives are completely free to play solo or squad-up across San Paro.\n"
            "> **03.** Register your in-game callsign and validate onboarding to access all secure channels."
        ),
        color=0xD4AF37
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

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
        title="🛠️ X Y Z // SAN PARO LOADOUT STUDIO 🛠️",
        description=(
            "> **TACTICAL ARMAMENT // APB:Db DATABASE INTEGRATION**\n"
            "> *Welcome to the syndicate elite loadout studio. Configure your primary firearm, core modifications, "
            "secondary weapon, and tactical gear for Citadel EU district dominance.*\n\n"
            "---\n\n"
            "### ⚙️ **OPERATIONAL PROTOCOL**\n"
            "- Click **`Initialize Loadout Studio Terminal`** below to open the secure selection interface.\n"
            "- Select your primary weapon and corresponding modifications (slots adapt automatically).\n"
            "- Click **Next** to select your secondary weapon and tactical grenade.\n"
            "- Broadcast your complete loadout preset to `🛠️│armory-builds`.*\n\n"
            "---\n"
            "> *« Superior firepower and flawless preparation are the keys to controlling San Paro. »*"
        ),
        color=0xD4AF37,
        timestamp=discord.utils.utcnow()
    )
    embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
    embed.set_footer(text="San Paro Armory Core • X Y Z Syndicate Infrastructure")
    
    await interaction.response.send_message("✅ Loadout Studio terminal successfully deployed.", ephemeral=True)
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

@client.tree.command(name="updatetickets", description="[ADMIN] Deploys the official support ticket panel.")
@app_commands.checks.has_permissions(administrator=True)
async def slash_updatetickets(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚡ X Y Z // SUPPORT & ASSISTANCE TERMINAL ⚡",
        description=(
            f"> **SECURE TRANSMISSION // SAN PARO ASSISTANCE**\n"
            f"> *Do you require direct assistance from the command staff, have a question regarding clan operations, "
            f"or wish to report an issue? Open a secure, encrypted ticket below.*\n\n"
            f"---\n\n"
            f"### 🛡️ **OPERATIONAL PROTOCOL**\n"
            f"- Click the **`Create Secure Ticket`** button below to open a private channel visible only to you and the staff.\n"
            f"- Do not open multiple tickets unnecessarily. Maintain absolute discipline.\n\n"
            f"---\n"
            f"> *« Precision in communication ensures syndicate dominance. »*"
        ),
        color=0xD4AF37,
        timestamp=discord.utils.utcnow()
    )
    embed.set_footer(text="X Y Z Syndicate Support Matrix • Citadel EU")

    target_channel = interaction.guild.get_channel(CHANNELS.get("support")) or interaction.channel
    await target_channel.send(embed=embed, view=TicketCreateView())
    await interaction.response.send_message("✅ Support ticket panel successfully deployed.", ephemeral=True)

@client.tree.command(name="updateticketrules", description="[ADMIN] Publishes the official support ticket rules.")
@app_commands.checks.has_permissions(administrator=True)
async def slash_updateticketrules(interaction: discord.Interaction):
    target_channel_id = CHANNELS.get("ticket_rules")
    target_channel = interaction.guild.get_channel(target_channel_id)

    if not target_channel:
        await interaction.response.send_message(
            "❌ **Configuration Error:** Channel `ticket-rules` not found in .env file.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="⚡ X Y Z // SECURE SUPPORT & TICKET REGULATIONS ⚡",
        description=(
            "> **SECURITY DIRECTIVE // MAINFRAME ENCRYPTION ACTIVE**\n"
            "> *Welcome operatives. This communication channel is dedicated to resolving operational issues, "
            "administrative queries, and official reports. To maintain absolute order and efficiency within "
            "the syndicate, strict protocols apply to all support transmissions.*\n\n"
            "---\n\n"
            "### 🛡️ **01. PURPOSE OF SUPPORT TICKETS**\n"
            "- Use tickets only for **legitimate matters** (e.g., role attribution issues, partnership inquiries, "
            "reporting severe rule violations, or technical assistance with bot commands).\n"
            "- Do not open a ticket for trivial questions or general chat; use the public Citadel districts instead.\n\n"
            "### 💼 **02. CONDUCT & DISCIPLINE**\n"
            "- When a secure channel is opened, maintain professionalism and respect toward the command staff and officers.\n"
            "- Provide clear evidence, screenshots, or detailed explanations regarding your request immediately to speed up the resolution process.\n\n"
            "### ⏱️ **03. SPAM & ABUSE**\n"
            "- **Do not open multiple tickets** for the same request.\n"
            "- Spamming, trolling, or opening fake tickets will result in immediate administrative sanctions and potential restriction from syndicate infrastructure (`[Blacklisted]`).\n\n"
            "---\n"
            "> *« Precision in communication ensures syndicate dominance. Respect the protocol, and command will assist you. »*"
        ),
        color=0xD4AF37,
        timestamp=discord.utils.utcnow()
    )
    embed.set_footer(text="X Y Z Syndicate Support Rules • Citadel EU")

    await target_channel.send(embed=embed)
    await interaction.response.send_message("✅ Support ticket rules successfully published.", ephemeral=True)

@client.tree.command(name="updateranks", description="Publishes the official syndicate ranks directory.")
@app_commands.checks.has_permissions(administrator=True)
async def slash_updateranks(interaction: discord.Interaction):
    embed_part1 = discord.Embed(
        title="⚡ X Y Z // SYNDICATE DIRECTORY (PART 1) ⚡",
        description=(
            "> **SECURE TRANSMISSION // QUANTUM LINK: SECURED**\n"
            "> *Welcome to the official hierarchy of the syndicate. Discipline, operational loyalty, "
            "and absolute dominance over the streets of San Paro define your worth within our infrastructure.*\n\n"
            "---\n\n"
            "### 👑 SUPREME COMMAND & SYSTEM\n"
            "- **`👑・[Owner]`** — Absolute authority and supreme administration.\n"
            "- **`🤖・[XYZ Bot]`** — Autonomous system entity managing live telemetry and security.\n"
            "- **`⚜️・[XYZ Architect]`** — Mastermind behind technological infrastructure and telemetry.\n"
            "- **`⚡・[Leader]`** — Supreme commander of clan operations and strategic decisions.\n"
            "- **`🛡️・[Officer]`** — Elite framework in charge of moderation and recruit training.\n\n"
            "---\n\n"
            "### 🛡️ SYNDICATE CORE & SECURITY\n"
            "- **`💀・[Member]`** — Fully validated official operative dedicated to San Paro.\n"
            "- **`🤝・[Special Guest]`** — Trusted friend or special guest allied with the syndicate.\n"
            "- **`⭐・[Pending Approval]`** — Operative under review in verification-logs pending roster check.\n"
            "- **`⚡・[Recruit]`** — Candidate undergoing strict probation under officer supervision.\n"
            "- **`➖・[Blacklisted]`** — Restricted security cell for rejected or isolated elements.\n"
            "- **`❌・[Denied]`** — Callsign unrecognized or rejected by command staff.\n\n"
            "---\n\n"
            "### ⚔️ TACTICAL DIVISIONS\n"
            "- **`🛡️・[Financial Expert]`** — Long-range combat specialist in Financial districts.\n"
            "- **`⚓・[Waterfront Specialist]`** — Close-quarters urban combat expert in Waterfront districts.\n"
            "- **`🏎️・[Wheelman]`** — Elite driver for high-speed getaways and tactical positioning.\n"
            "- **`🛡️・[Armorer & Designer]`** — Master of vehicle styling, custom symbols, and gear optimization.\n"
            "- **`🛡️・[Intel Scout]`** — Recon specialist for tracking telemetry and district status.\n"
            "- **`🛡️・[Enforcer Killer]`** — High-tier PvP elimination specialist.\n\n"
            "---\n\n"
            "### 🏆 ACHIEVEMENTS & ELITE RANKS\n"
            "- **`⚡・[XYZ Apex Predator]`** — Supreme decoration awarded to internal tournament champions.\n"
            "- **`🛡️・[Syndicate Phantom]`** — Elite title earned through high-risk infiltration and sabotage.\n"
            "- **`⭐・[Task Force Commander]`** — Command rank assigned to lead major district campaigns.\n"
            "- **`☀️・[XYZ Veteran]`** — Respected long-standing member valued for deep combat experience.\n"
            "- **`🛡️・[Reserve Force]`** — Trusted veterans currently on tactical standby.\n\n"
            "---\n\n"
            "### ⭐ COMMUNITY & PERKS\n"
            "- **`🚀・[XYZ Booster]`** — Active supporters propelling server infrastructure.\n"
            "- **`🎧・[Frequency DJ]`** — Sound maestro managing audio streams in `#frequency`.\n"
            "- **`🛡️・[The Syndicate Oracle]`** — Unique supreme entity embodying the ultimate lore."
        ),
        color=0xD4AF37
    )

    embed_part2 = discord.Embed(
        title="⚡ X Y Z // LEVEL MATRIX (PART 2) ⚡",
        description=(
            "### ⚡ THE MAINFRAME LEVEL MATRIX // TIER 1 TO 100\n"
            "- **`⭐・[Lvl 01-04] Outer Fringe Civilian`** — Newly arrived, off the syndicate radar.\n"
            "- **`⭐・[Lvl 05] Syndicate Prospect`** — First contact established, street trials.\n"
            "- **`⭐・[Lvl 06-14] Street Runner`** — Running packages and basic district survival.\n"
            "- **`🛡️・[Lvl 15] Underground Operative`** — Officially recognized operation asset.\n"
            "- **`🛡️・[Lvl 16-24] Block Operative`** — Securing territory and neighborhood sectors.\n"
            "- **`🛡️・[Lvl 25] Syndicate Specialist`** — Specialized tactical combat gear.\n"
            "- **`🛡️・[Lvl 26-39] District Guardian`** — Securing syndicate law across sectors.\n"
            "- **`⚡・[Lvl 40] Sector Vanguard`** — Leading tactical units during skirmishes.\n"
            "- **`⚡・[Lvl 41-54] Black Market Operative`** — Managing contraband and high-value arms.\n"
            "- **`🟠・[Lvl 55] Syndicate Veteran`** — Seasoned combatant with deep experience.\n"
            "- **`🛡️・[Lvl 56-69] Elite Executioner`** — Feared hitman with zero-failure extractions.\n"
            "- **`❌・[Lvl 70] Syndicate Commander`** — Directing squad tactics and dominance.\n"
            "- **`❌・[Lvl 71-84] Shadow Strike Lead`** — Spearheading covert operations and sabotage.\n"
            "- **`🔥・[Lvl 85] Mainframe Phantom`** — Bridging digital infiltration and street warfare.\n"
            "- **`🔥・[Lvl 86-94] Apex Vanguard`** — Unstoppable force dictating the pace of combat.\n"
            "- **`💀・[Lvl 95] Syndicate Overlord`** — Absolute authority over regional operations.\n"
            "- **`💀・[Lvl 96-99] Syndicate Prime`** — Inner circle of supreme syndicate leadership.\n"
            "- **`⚡👑・[Lvl 100] Syndicate Legend`** — The pinnacle of achievement, immortalized in the central mainframe.\n\n"
            "---\n"
            "> *« Know your rank, honor your callsign. Click below to proceed to the rules. »*"
        ),
        color=0xD4AF37
    )
    
    await interaction.response.send_message("✅ Ranks directory successfully generated.", ephemeral=True)
    await interaction.channel.send(embeds=[embed_part1, embed_part2], view=RanksOnboardingView())

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
    await interaction.response.send_message("✅ Server rules successfully generated.", ephemeral=True)
    await interaction.channel.send(embed=embed, view=VerificationView())

client.run(TOKEN)