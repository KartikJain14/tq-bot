import discord
from discord.ext import commands
import re
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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
        
        html_content = html_template.replace("{{name}}", name).replace("{{team_no}}", team_no).replace("{{invite_link}}", invite_link)
        
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = to_email
        msg['Subject'] = "🟣 Cyber Cypher 4.0 Invitation"
        msg.attach(MIMEText(html_content, 'html'))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_username, to_email, msg.as_string())
        server.quit()
        
        print(f"Email sent successfully to {to_email} with invite link: {invite_link}")
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")

@bot.command()
async def register(ctx, name: str = "", email: str = "", team_number: str = ""):
    if ctx.channel.id != bot_channel:
        await ctx.send("You cannot run this command here.", delete_after=5)
        return

    if not name or not email or not team_number:
        await ctx.send("Incorrect usage. Use: `!register <name> <email> <team_id>`")
        return

    name = name.capitalize()

    if not is_valid_email(email):
        await ctx.send("Invalid email address!")
        return

    if not (team_number.startswith("A") or team_number.startswith("B")) or len(team_number) != 4:
        await ctx.send("Invalid team number format! Use 'A001' or 'B302'.")
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
    send_email(to_email=email, name=name, team_no=team_number, invite_link=invite_link)
    await ctx.send(f"{name} - {team_number} - `{invite_link}`.")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.channel.id == webhook_channel_id:
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
                send_email(to_email=email, name=name, team_no=team_number, invite_link=invite_link)
                await message.channel.send(f"{name} - {team_number} - `{invite_link}`.")
            
            except Exception as e:
                await message.channel.send(f"An error occurred: {e}")
                print(f"Error handling webhook command: {e}")

    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

bot.run(BOT_TOKEN)
