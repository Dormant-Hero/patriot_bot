import psycopg
from config import DB_CONNECTION_STRING
from icecream import ic
# import logging


# logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")

# logging.getLogger("psycopg").setLevel(logging.DEBUG)

# psycopg.connect("host=192.0.2.1,localhost connect_timeout=10")


def fetch_all_commands_db():
    with psycopg.connect(DB_CONNECTION_STRING) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT command_name, command_description, command_response FROM bot_commands")
            return cur.fetchall()

def fetch_all_embed_commands_db():
    with psycopg.connect(DB_CONNECTION_STRING) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT command_name, command_title, command_description, embed_color, embed_image, embed_help FROM bot_commands_embed")
            return cur.fetchall()

def add_command_db(command_name, command_description, command_response):
    with psycopg.connect(DB_CONNECTION_STRING) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO bot_commands (command_name, command_description, command_response) VALUES (%s, %s, %s)",
                (command_name.lower(), command_description, command_response)
            )
            conn.commit()


def update_command_db(command_name, command_response, command_description):
    with psycopg.connect(DB_CONNECTION_STRING) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE bot_commands
                SET command_response = %s, command_description = %s
                WHERE lower(command_name) = lower(%s)
                """,
                (command_response, command_description, command_name.lower())
            )
            conn.commit()

def add_embed_command_db(command_name, command_title, command_content, embed_colour, embed_image, embed_description):
      with psycopg.connect(DB_CONNECTION_STRING) as conn:
            ic(command_name, command_title, command_content, embed_colour, embed_image, embed_description)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO bot_commands_embed (command_name, command_title, command_description, embed_color, embed_image, embed_help)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (command_name.lower(), command_title, command_content, embed_colour, embed_image, embed_description)
                )
                conn.commit()
# command content is basically labelled as command description in the db. I will probably change that at some stage.

def update_emb_command_db(command_name, emb_title, emb_description, emb_content, emb_colour, emb_image_url):
    with psycopg.connect(DB_CONNECTION_STRING) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE bot_commands_embed
                SET command_title=%s, command_description=%s, embed_color=%s, embed_image=%s, embed_help=%s
                WHERE lower(command_name) = lower(%s)
                """,
                (emb_title, emb_content, emb_colour, emb_image_url, emb_description, command_name.lower())
            )
            conn.commit()
        
def existing_command_db(command_name, embed):
    with psycopg.connect(DB_CONNECTION_STRING) as conn:
        with conn.cursor() as cur:
            if not embed:
                cur.execute("SELECT id FROM bot_commands WHERE command_name = %s", (command_name,))
                existing = cur.fetchone()
                return existing
            else:
                cur.execute("SELECT id FROM bot_commands_embed WHERE command_name = %s", (command_name,))
                existing = cur.fetchone()
                return existing

def in_other_table_db(command_name, embed=False):
     with psycopg.connect(DB_CONNECTION_STRING) as conn:
            with conn.cursor() as cur:
                if embed:
                    cur.execute("SELECT id FROM bot_commands WHERE command_name = %s", (command_name,))
                    existing = cur.fetchone()
                    return existing
                else:
                    cur.execute("SELECT id FROM bot_commands_embed WHERE command_name = %s", (command_name,))
                    existing = cur.fetchone()
                    return existing