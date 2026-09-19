CREATE TABLE bot_commands (
    id SERIAL PRIMARY KEY,
    command_name VARCHAR(100) NOT NULL UNIQUE,
    command_description TEXT,
    command_response TEXT
)

CREATE TABLE bot_commands_embed (
    id SERIAL PRIMARY KEY,
    command_name VARCHAR(100) NOT NULL UNIQUE,
    command_title TEXT,
    command_description TEXT,
    embed_color INT,
    embed_image TEXT,
    embed_help TEXT
)