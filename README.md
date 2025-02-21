Cusotmised Discord bot for Taqneeq 17.0's Cyber Cypher - NMIMS' official hackathon.
This bot handles 1100+ participants that participated for the hackathon.

Usage:
`!register Kartik kartik@tq.com B004`

This bot does:
1. Give Member the participant role.
2. Rename the participants as [🧠] <Team ID> - <FName>
3. Create / Edit voice respective team voice channel to give access to the specific channel the participant belongs to. (The voice channels are configured to also allow specific role to view and connect to channels for random inspections)

Why?
This was made to manage and moderate the incoming huge crowd of participants and eliminate the use of RD (registration desk) where OC (organizing committe) have to manually create, assign, rename the members which would be manual labour and time consuming.
This bot revolutionizes the way hackathons are hosted virtually on discord and is to set a new standard in the college communities.

Challenges Faced:
Having a huge crowd, initially the bot was planend to create 50 channels each category using initialization scripts (discord limits channels in each category) with configuring the team role and a specific role to view and conenct to the channel.
But, discord limits 250 roles per server therefore this plan failed.
Later, channels were configured indivually to assign members and change their permissions indiviually while still allowing the oc specific role to view and connect to channels.

Automation:
The command `!register` still needed to be run therfore, we made and setup a script that would send webhooks every X seconds with the participant details in the correc format.

How it works:
Command gets the name, email and team-id and generates a unique invite link for each command and saves everything in MongoDB, the unique link is then returned in response.
When member joins the guild (server) an algorithm checks what possible invite code was used to join the guild by the member.
If the invite code exists in the database, the member is renamed to the correct format along with other details.
Then, it checks in respective category if a channel for the member's team id exists? If not, it creates one and initializes with the specific OC role to allow them too.
After the channel is found / created, it as edited to also allow the current member to view and conenect to that specific channel while the defualt role (@everyone) isn't allow to view or connect.

Featuring [WebApp](https://github.com/KartikJain14/tq-dc-bot-web) where the user is allowed to find their unique invite url.
