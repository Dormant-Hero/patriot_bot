# ![logo 4185b845](https://github.com/Dormant-Hero/SaveMGOLobbyBot/assets/79374258/11f754cb-aa63-4e83-adc5-6d780e334e11)

The official bot for the SaveMGO Discord (discord.gg/mgo2pc), the community
server for Metal Gear Online 2.

Admins can create and delete `!` commands from inside Discord itself. Commands
live in Postgres and get registered at runtime, so adding one doesn't need a
restart.

<img width="900" height="326" alt="demo" src="https://github.com/user-attachments/assets/a33d75dc-9567-4a47-b874-623fc5a216e0" />

## What it does

Admins:
- `/add_command` creates a plain text `!command`
- `/add_embed_command` does the same but posts an embed, with a title, colour and image
- `/delete_command` removes either kind

Everyone:
- Use any `!command` an admin has made
- `/link` gives you a link to an MGO2 character profile

Automatic:
- New members get the Patriots role when they join

## Not here yet

- Lobby bot
- `!help` with search and paginated embeds
- `!error` for looking up common game errors

## Running it yourself

Not really built for anyone else to use, but nothing stops you.

1. `pip install -r requirements.txt`
2. Fill in `.env.example` and rename it `.env`
3. Create a Postgres database and run `schema.sql` against it
4. `python main.py`
5. Run `!sync` once as the owner so Discord picks up the slash commands. You
   will probably have to restart your Discord client before they show up. If
   they still don't appear, check they're enabled under Server Settings >
   Integrations.

I run mine on an Ubuntu server over SSH, in a venv.
