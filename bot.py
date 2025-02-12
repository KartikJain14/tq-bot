import discord
from discord.ext import commands
import re
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import asyncio
import sqlite3

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

client = MongoClient(os.getenv("MONGODB_URI"))
db = client["discord_bot"]
participants_collection = db["participants"]
smtp_server = os.getenv("SMTP_SERVER") or "smtp.mailgun.org"
smtp_port = os.getenv("SMTP_PORT") or 587
smtp_username = os.getenv("SMTP_USERNAME") or "noreply@taqneeqfest.com"
smtp_password = os.getenv("SMTP_PASSWORD") or "password"

rule_channel = 1335346410429878287
bot_channel = 1335355212659032135
webhook_channel_id = 1338595040531845130

category_a1 = 1337824768493355230
category_a2 = 1338163500408635473
category_a3 = 1338164494618198066
category_a4 = 1338164785128144966
category_b1 = 1335358954858876958
category_b2 = 1338165266806476882

EMOJIS = ["🤺", "🦾", "🦿"]

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def is_valid_email(email):
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None

async def generate_invite_link(channel):
    invite = await channel.create_invite(max_uses=2, unique=True)
    return invite.url

def send_email(to_email, name, team_no, invite_link):
    try:
        with open("email.html", "r", encoding="utf-8") as file:
            html_template = file.read()

        # Replace placeholders in the template with actual data
        html_content = html_template.replace("{{name}}", name)
        html_content = html_content.replace("{{team_no}}", team_no)
        html_content = html_content.replace("{{invite_link}}", invite_link)

        # Set up the MIME object for email
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = to_email
        msg['Subject'] = "🟣 Cyber Cypher 4.0 Invitation"

        # Attach the HTML content
        msg.attach(MIMEText(html_content, 'html'))

        # Connect to the Mailgun SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Start TLS encryption
        server.login(smtp_username, smtp_password)  # Log in to the SMTP server

        # Send the email
        server.sendmail(smtp_username, to_email, msg.as_string())

        # Close the connection
        server.quit()

        print(f"Email sent successfully to {to_email} with invite link: `{invite_link}`")
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")

def save(to_email, name, team_no, invite_link):
    # Connect to SQLite database (or create one if it doesn't exist)
    conn = sqlite3.connect('team_invites.db')
    cursor = conn.cursor()

    # Create table if it doesn't exist already
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS invites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        to_email TEXT NOT NULL,
        name TEXT NOT NULL,
        team_no INTEGER NOT NULL,
        invite_link TEXT NOT NULL
    )
    ''')

    # Insert the provided data into the table
    cursor.execute('''
    INSERT INTO invites (to_email, name, team_no, invite_link)
    VALUES (?, ?, ?, ?)
    ''', (to_email, name, team_no, invite_link))

    # Commit the transaction and close the connection
    conn.commit()
    conn.close()

@bot.command()
async def register(ctx, name: str = "", email: str="", team_number: str = ""):
    if ctx.channel.id != bot_channel:
        await ctx.send("You cannot run this command here.", delete_after=5)
        return

    if name == "" or team_number == "" or email == "":
        await ctx.send("Incorrect usage, please try again with the correct format: `!register <name> <email> <team_id (A001)>`")
        return
    name = name.capitalize()

    if not (team_number.startswith("A") or team_number.startswith("B")) or len(team_number) != 4:
        await ctx.send(f"Invalid team number format! Please enter in format like 'A001' or 'B302'.")
        return
    
    if not is_valid_email(email):
        await ctx.send("Invalid email address provided!")
        return

    invite_channel = ctx.guild.get_channel(rule_channel)
    invite_link = await generate_invite_link(invite_channel)

    participant = {
        "name": name,
        "team_number": team_number,
        "email": email,
        "invite_link": invite_link
    }
    participants_collection.insert_one(participant)

    save(to_email=email, name=name, team_no=team_number, invite_link=invite_link)

    await ctx.send(f"{name} - {team_number} - `{invite_link}`.")

@bot.event
async def on_member_join(member):
    invites = await member.guild.invites()
    used_invite = None

    for invite in invites:
        if invite.inviter == bot.user and invite.uses == 1:
            used_invite = invite
            break
    
    # oc_role = discord.utils.get(member.guild.roles, name="OC 🧙‍♂️")

    if not used_invite:
        # if oc_role:
        #     member.add_roles(oc_role)
        print("No valid invite found!")
        return
    
    participant = participants_collection.find_one({"invite_link": used_invite.url})
    
    try:
        await used_invite.delete()
    except discord.NotFound:
        print(f"Invite {used_invite.url} not found on Discord's servers (might already be deleted).")

    participant_role = discord.utils.get(member.guild.roles, name="Participants 💻")

    if not participant:
        if participant_role:
            await member.add_roles(participant_role)
        await member.send("I faced a problem while trying to register you. Please contact the organizers for help.")
        print(f"Participant with invite link: {used_invite.url} not found in the database!")
        return

    if participant_role:
        await member.add_roles(participant_role)

    await member.edit(nick=f"[🧠] {participant['team_number']} - {participant['name']}")

    await member_handler(member, participant["team_number"])


@bot.command()
async def purge(ctx, amount: int = 10):
    if not ctx.author.guild_permissions.manage_messages:
        await ctx.send("You do not have the required permissions to use this command.", delete_after=5)
        return

    try:
        if amount < 1:
            await ctx.send("Please specify a positive number of messages to delete.")
            return

        if amount > 100:
            await ctx.send("You can only delete up to 100 messages at a time.")
            return

        # Delete the messages
        deleted = await ctx.channel.purge(limit=amount)
        await ctx.send(f"Successfully deleted {len(deleted)} messages.", delete_after=5)

    except Exception as e:
        await ctx.send(f"An error occurred while trying to delete messages: {e}")

@bot.event
async def on_command_error(ctx, error):
    await ctx.send(error)
    await ctx.send("Please contact <@!591970092720324610> for help.")
    print(error)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    bot.loop.create_task(delete_used_invites())

async def member_handler(member, team_id):
    channel = await get_or_make_channel(team_id, member.guild)
    await channel.set_permissions(member, view_channel=True, connect=True)

async def get_or_make_channel(team_id, guild):
    team_type = team_id[0]
    team_no = int(team_id[1:])
    category = None

    if team_no < 1 or team_no > 200:
        raise ValueError("Invalid team number provided!")
    
    if team_type == "A":
        if team_no <= 50:
            category = guild.get_channel(category_a1)
        elif team_no <= 100:
            category = guild.get_channel(category_a2)
        elif team_no <= 150:
            category = guild.get_channel(category_a3)
        else:
            category = guild.get_channel(category_a4)
    elif team_type == "B":
        if team_no <= 50:
            category = guild.get_channel(category_b1)
        else:
            category = guild.get_channel(category_b2)
    
    if not category or not isinstance(category, discord.CategoryChannel):
        raise ValueError(f"Category not found or is not a Category Channel: {category}")

    channel_name = f"Team {team_type}{str(team_no).zfill(3)} {EMOJIS[team_no % 3]}"
    for channel in category.channels:
        if channel.name == channel_name:
            return channel

    helper_role = guild.get_role(1336749195100688447)
    if not helper_role:
        raise ValueError("Participant role not found! Please check the role ID.")

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False, connect=False),
        helper_role: discord.PermissionOverwrite(view_channel=True, connect=True),
    }

    channel = await guild.create_voice_channel(channel_name, category=category, overwrites=overwrites)
    return channel

@bot.event
async def on_message(message):
    # Ignore bot messages
    if message.author == bot.user:
        return

    # Check if the message is from a webhook in the specified channel
    if message.channel.id == webhook_channel_id and message.webhook_id:
        # Extract and handle the webhook message content
        if message.content.startswith("!register"):
            try:
                parts = message.content.split()
                if len(parts) != 4:
                    await message.channel.send("Invalid format. Use: `!register <Name> <Email> <TeamId>`")
                    return

                name, email, team_number = parts[1], parts[2], parts[3]

                if not is_valid_email(email):
                    await message.channel.send(f"Invalid email address: {email}")
                    return

                if not (team_number.startswith("A") or team_number.startswith("B")) or len(team_number) != 4:
                    await message.channel.send(f"Invalid team number format: {team_number}. Use 'A001' or 'B302'.")
                    return

                invite_channel = message.guild.get_channel(rule_channel)
                invite_link = await generate_invite_link(invite_channel)

                participant = {
                    "name": name.capitalize(),
                    "team_number": team_number,
                    "email": email,
                    "invite_link": invite_link
                }
                participants_collection.insert_one(participant)
                save(to_email=email, name=name, team_no=team_number, invite_link=invite_link)
                await message.channel.send(f"{name} - {team_number} - `{invite_link}`.")
            
            except Exception as e:
                await message.channel.send(f"An error occurred: {e}")
                print(f"Error handling webhook command: {e}")

    # Ensure bot commands still work by processing them after handling the webhook
    await bot.process_commands(message)

async def delete_used_invites():
    await bot.wait_until_ready()  # Ensure the bot is fully ready before starting

    while True:
        try:
            # Get all invites in the server
            for guild in bot.guilds:
                invites = await guild.invites()

                for invite in invites:
                    # Check if the invite was created by the bot and if it has been used more than once
                    if invite.inviter == bot.user and invite.uses > 1:
                        # Delete the invite
                        await invite.delete()
                        print(f"Deleted invite {invite.url} created by {invite.inviter} with {invite.uses} uses.")
        except Exception as e:
            print(f"An error occurred while checking invites: {e}")
        
        # Wait for 30 seconds before checking again
        await asyncio.sleep(30)


bot.run(BOT_TOKEN)