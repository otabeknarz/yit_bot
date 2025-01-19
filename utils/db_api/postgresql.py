from typing import Union

import asyncpg
from asyncpg import Connection
from asyncpg.pool import Pool

from data import config
from data.config import lang_file


class Database:

    def __init__(self):
        self.pool: Union[Pool, None] = None

    async def create(self):
        self.pool = await asyncpg.create_pool(
            user=config.DB_USER,
            password=config.DB_PASS,
            host=config.DB_HOST,
            port=6432,
            database=config.DB_NAME,
        )

    async def execute(
        self,
        command,
        *args,
        fetch: bool = False,
        fetchval: bool = False,
        fetchrow: bool = False,
        execute: bool = False,
        executemany: bool = False,
    ):
        async with self.pool.acquire() as connection:
            connection: Connection
            async with connection.transaction():
                if fetch:
                    result = await connection.fetch(command, *args)
                elif fetchval:
                    result = await connection.fetchval(command, *args)
                elif fetchrow:
                    result = await connection.fetchrow(command, *args)
                elif execute:
                    result = await connection.execute(command, *args)
                elif executemany:

                    result = await connection.executemany(command, [*args])

            return result

    async def create_table_users(self):
        sql = """
        CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL UNIQUE,
        lang TEXT NOT NULL DEFAULT 'uz',
        status VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        unique_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        await self.execute(sql, execute=True)

    async def create_table_groups(self):
        sql = """
        CREATE TABLE IF NOT EXISTS groups (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL UNIQUE,
        status VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        await self.execute(sql, execute=True)

    async def create_table_settings(self):
        sql = """
        CREATE TABLE IF NOT EXISTS settings (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        value VARCHAR(255) NOT NULL
        );
        """
        await self.execute(sql, execute=True)

    async def create_table_channels(self):
        sql = """
        CREATE TABLE IF NOT EXISTS channels (
        id SERIAL PRIMARY KEY,
        channel_id VARCHAR(255) NOT NULL,
        channel_link TEXT NOT NULL
        );
        """
        await self.execute(sql, execute=True)

    async def create_table_join_requests(self):
        sql = """
        CREATE TABLE IF NOT EXISTS join_requests (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        chat_id BIGINT NOT NULL
        );
        """
        await self.execute(sql, execute=True)

    async def create_table_mailing(self):
        sql = """
        CREATE TABLE IF NOT EXISTS mailing (
        id BIGSERIAL PRIMARY KEY,
        status BOOLEAN NOT NULL DEFAULT TRUE,
        user_id BIGINT,
        message_id BIGINT,
        reply_markup TEXT,
        mail_type TEXT NOT NULL,
        "offset" BIGINT NOT NULL DEFAULT 0,
        send BIGINT NOT NULL DEFAULT 0,
        not_send BIGINT NOT NULL DEFAULT 0,
        "type" TEXT NOT NULL,
        location TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
        await self.execute(sql, execute=True)

    async def create_table_medias(self):
        sql = """
        CREATE TABLE IF NOT EXISTS medias (
        id SERIAL PRIMARY KEY,
        link TEXT,
        file_id TEXT,
        content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        await self.execute(sql, execute=True)

    async def create_table_audios(self):
        sql = """
        CREATE TABLE IF NOT EXISTS audios (
        id SERIAL PRIMARY KEY,
        title TEXT,
        music_id TEXT,
        file_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        await self.execute(sql, execute=True)

    async def create_table_tops(self):
        sql = """
        CREATE TABLE IF NOT EXISTS tops (
        id SERIAL PRIMARY KEY,
        title TEXT,
        music_id TEXT,
        country TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        await self.execute(sql, execute=True)

    async def create_table_posts(self):
        sql = """
        CREATE TABLE IF NOT EXISTS posts (
        id SERIAL PRIMARY KEY,
        file_id TEXT,
        caption TEXT,
        content TEXT,
        code TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        await self.execute(sql, execute=True)

    async def create_table_sps(self):
        sql = """
        CREATE TABLE IF NOT EXISTS sps (
        id SERIAL PRIMARY KEY,
        file_id TEXT,
        caption TEXT,
        content TEXT,
        reply_markup TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        await self.execute(sql, execute=True)

    async def create_table_ads(self):
        sql = """
        CREATE TABLE IF NOT EXISTS ads (
        id SERIAL PRIMARY KEY,
        ads_text TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        await self.execute(sql, execute=True)

    async def create_table_referals(self):
        sql = """
        CREATE TABLE IF NOT EXISTS referals (
        id SERIAL PRIMARY KEY,
        code TEXT,
        members INTEGER DEFAULT 1,
        days INTEGER DEFAULT 1,
        weekly INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        await self.execute(sql, execute=True)

    async def create_table_bots(self):
        sql = """
        CREATE TABLE IF NOT EXISTS bots (
        id SERIAL PRIMARY KEY,
        bot_token TEXT NOT NULL,
        bot_link TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        await self.execute(sql, execute=True)

    async def create_table_admins(self):
        sql = """
        CREATE TABLE IF NOT EXISTS admins (
        id SERIAL PRIMARY KEY,
        user_id TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        await self.execute(sql, execute=True)

    @staticmethod
    def format_args(sql, parameters: dict):
        sql += " AND ".join(
            [f"{item} = ${num}" for num, item in enumerate(parameters.keys(), start=1)]
        )
        return sql, tuple(parameters.values())

    # Todo: add function
    async def add_user(self, user_id, status="active"):
        sql = "INSERT INTO users (user_id, status) VALUES ($1, $2)"
        return await self.execute(sql, user_id, status, fetchrow=True)

    async def add_bot(self, bot_token, bot_link):
        sql = "INSERT INTO bots (bot_token, bot_link) VALUES ($1, $2)"
        return await self.execute(sql, bot_token, bot_link, fetchrow=True)

    async def add_settings(self):
        sql = "INSERT INTO settings (name, value) VALUES ('Channel', 'False');"
        return await self.execute(sql, fetchrow=True)

    async def add_group(self, user_id, status="active"):
        sql = "INSERT INTO groups (user_id, status) VALUES ($1, $2)"
        return await self.execute(sql, user_id, status, fetchrow=True)

    async def add_ads(self, ads_text):
        sql = "INSERT INTO ads (ads_text) VALUES ($1)"
        return await self.execute(sql, ads_text, fetchrow=True)

    async def add_admins(self, user_id):
        sql = "INSERT INTO admins (user_id) VALUES ($1)"
        return await self.execute(sql, user_id, fetchrow=True)

    async def add_referals(self, code):
        sql = "INSERT INTO referals (code) VALUES ($1)"
        return await self.execute(sql, code, fetchrow=True)

    async def add_medias(self, link, file_id, content="video"):
        sql = "INSERT INTO medias (link, file_id, content) VALUES ($1, $2, $3)"
        return await self.execute(sql, link, file_id, content, fetchrow=True)

    async def add_posts(self, file_id, caption, content, code):
        sql = "INSERT INTO posts (file_id, caption, content, code) VALUES ($1, $2, $3, $4)"
        return await self.execute(sql, file_id, caption, content, code, fetchrow=True)

    async def add_sps(self, file_id, caption, content, reply_markup):
        sql = "INSERT INTO sps (file_id, caption, content, reply_markup) VALUES ($1, $2, $3, $4)"
        return await self.execute(
            sql, file_id, caption, content, reply_markup, fetchrow=True
        )

    async def add_audios(self, title, music_id, file_id):
        sql = "INSERT INTO audios (title, music_id, file_id) VALUES ($1, $2, $3)"
        return await self.execute(sql, title, music_id, file_id, fetchrow=True)

    async def add_tops(self, data):
        truncate_sql = "TRUNCATE tops"
        await self.execute(truncate_sql, execute=True)
        sql = "INSERT INTO tops (title, music_id, country) VALUES ($1, $2, $3)"
        return await self.execute(sql, *data, executemany=True)

    async def add_channel(self, channel_id, channel_link):
        sql = (
            "INSERT INTO channels (channel_id, channel_link) VALUES($1, $2) returning *"
        )
        return await self.execute(sql, channel_id, channel_link, fetchrow=True)

    async def add_join_requests(self, user_id, chat_id):
        sql = "INSERT INTO join_requests (user_id, chat_id) VALUES($1, $2) returning *"
        return await self.execute(sql, user_id, chat_id, fetchrow=True)

    async def add_new_mailing(
        self, user_id, message_id, reply_markup, mail_type, type, location
    ):
        sql = "INSERT INTO mailing (user_id, message_id, reply_markup, mail_type, type, location) VALUES ($1, $2, $3, $4, $5, $6) RETURNING *"
        return await self.execute(
            sql,
            user_id,
            message_id,
            reply_markup,
            mail_type,
            type,
            location,
            fetchrow=True,
        )

    # Todo: select function
    async def select_user(self, **kwargs):
        sql = "SELECT * FROM users WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        return await self.execute(sql, *parameters, fetchrow=True)

    async def select_post(self, **kwargs):
        sql = "SELECT * FROM posts WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        return await self.execute(sql, *parameters, fetchrow=True)

    async def select_referal(self, **kwargs):
        sql = "SELECT * FROM referals WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        return await self.execute(sql, *parameters, fetchrow=True)

    async def select_admin(self, **kwargs):
        sql = "SELECT * FROM admins WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        return await self.execute(sql, *parameters, fetchrow=True)

    async def select_bot(self, **kwargs):
        sql = "SELECT * FROM bots WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        return await self.execute(sql, *parameters, fetchrow=True)

    async def select_audio(self, **kwargs):
        sql = "SELECT * FROM audios WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        return await self.execute(sql, *parameters, fetchrow=True)

    async def select_group(self, **kwargs):
        sql = "SELECT * FROM groups WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        return await self.execute(sql, *parameters, fetchrow=True)

    async def select_join_requests(self, **kwargs):
        sql = "SELECT * FROM join_requests WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        return await self.execute(sql, *parameters, fetchrow=True)

    async def get_user_lang(self, **kwargs):
        sql = "SELECT lang FROM users WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        return await self.execute(sql, *parameters, fetchrow=True)

    # Todo: update function
    async def update_mailing_status(self, status, id):
        sql = "UPDATE mailing SET status=$1 WHERE id=$2"
        return await self.execute(sql, status, id, execute=True)

    async def update_referals_member(self, days, weekly, members, code):
        sql = "UPDATE referals SET days=$1, weekly=$2, members=$3 WHERE code=$4"
        return await self.execute(sql, days, weekly, members, code, execute=True)

    async def update_mailing_results(self, send, not_send, offset, id):
        sql = """UPDATE mailing SET send=$1, not_send=$2, "offset"=$3 WHERE id=$4"""
        return await self.execute(sql, send, not_send, offset, id, execute=True)

    async def update_user_status(self, status, user_id):
        sql = "UPDATE users SET status=$1 WHERE user_id=$2"
        return await self.execute(sql, status, user_id, execute=True)

    async def update_user_time(self, user_id):
        sql = "UPDATE users SET unique_at = CURRENT_TIMESTAMP WHERE user_id=$1"
        return await self.execute(sql, user_id, execute=True)

    async def update_user_lang(self, lang, user_id):
        sql = "UPDATE users SET lang=$1 WHERE user_id=$2"
        return await self.execute(sql, lang, user_id, execute=True)

    async def update_mailling_table_status(self, table, status, user_id):
        sql = "UPDATE {} SET status=$1 WHERE user_id=$2".format(table)
        return await self.execute(sql, status, user_id, execute=True)

    async def update_settings_status(self, id, value):
        sql = "UPDATE settings SET value=$1 WHERE id=$2"
        return await self.execute(sql, value, id, execute=True)

    async def update_link_members(self):
        sql = "UPDATE referals SET days = 0"
        return await self.execute(sql, execute=True)

    async def update_link_members_weekly(self):
        sql = "UPDATE referals SET weekly = 0"
        return await self.execute(sql, execute=True)

    # Todo: search function
    async def search_all_movies(self, name):
        sql = "SELECT * FROM movies WHERE name ILIKE $1"
        return await self.execute(sql, f"%{name.lower()}%", fetch=True)

    async def search_all_series(self, name):
        sql = "SELECT * FROM series WHERE name ILIKE $1"
        return await self.execute(sql, f"%{name.lower()}%", fetch=True)

    async def select_all_channels(self):
        sql = "SELECT * FROM channels"
        return await self.execute(sql, fetch=True)

    async def select_all_admins(self):
        sql = "SELECT * FROM admins"
        return await self.execute(sql, fetch=True)

    async def select_all_ads(self):
        sql = "SELECT * FROM ads"
        return await self.execute(sql, fetch=True)

    async def select_all_medias(self, **kwargs):
        sql = "SELECT * FROM medias WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        return await self.execute(sql, *parameters, fetch=True)

    async def select_tops(self, **kwargs):
        sql = "SELECT * FROM tops WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        return await self.execute(sql, *parameters, fetchrow=True)

    async def select_all_bots(self):
        sql = "SELECT * FROM bots"
        return await self.execute(sql, fetch=True)

    async def select_all_tops(self, limit, country, offset=0):
        sql = "SELECT * FROM tops WHERE country = $2 ORDER BY id LIMIT $1 OFFSET $3;"
        return await self.execute(sql, limit, country, offset, fetch=True)

    async def select_all_referals(self, limit, offset=0):
        sql = """
        SELECT * FROM referals
        ORDER BY members DESC, id
        LIMIT $1 OFFSET $2;
        """
        return await self.execute(sql, limit, offset, fetch=True)

    async def select_media(self, **kwargs):
        sql = "SELECT * FROM medias WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        return await self.execute(sql, *parameters, fetchrow=True)

    async def select_settings(self):
        sql = "SELECT * FROM settings"
        return await self.execute(sql, fetchrow=True)

    async def select_sps(self):
        sql = "SELECT * FROM sps"
        return await self.execute(sql, fetchrow=True)

    async def truncate_sps(self):
        truncate_sql = "TRUNCATE sps"
        return await self.execute(truncate_sql, execute=True)

    async def select_channels(self, **kwargs):
        sql = "SELECT * FROM channels WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        return await self.execute(sql, *parameters, fetchrow=True)

    async def select_mailing(self):
        sql = "SELECT * FROM mailing"
        return await self.execute(sql, fetchrow=True)

    async def select_users_mailing(self, offset, status="active"):
        sql = "SELECT * FROM users WHERE status = $2 ORDER BY id OFFSET $1;"
        return await self.execute(sql, offset, status, fetch=True)

    async def select_users_location_mailing(
        self, offset, status="active", location="uz"
    ):
        sql = (
            "SELECT * FROM users WHERE status = $2 AND lang = $3 ORDER BY id OFFSET $1;"
        )
        return await self.execute(sql, offset, status, location, fetch=True)

    async def select_groups_mailing(self, offset, status="active"):
        sql = "SELECT * FROM groups WHERE status = $2 ORDER BY id OFFSET $1;"
        return await self.execute(sql, offset, status, fetch=True)

    # Todo: delete function
    async def delete_channel(self, **kwargs):
        sql = "DELETE FROM channels WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        await self.execute(sql, *parameters, execute=True)

    async def delete_ads(self, **kwargs):
        sql = "DELETE FROM ads WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        await self.execute(sql, *parameters, execute=True)

    async def delete_referal(self, **kwargs):
        sql = "DELETE FROM referals WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        await self.execute(sql, *parameters, execute=True)

    async def delete_bot(self, **kwargs):
        sql = "DELETE FROM bots WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        await self.execute(sql, *parameters, execute=True)

    async def delete_admin(self, **kwargs):
        sql = "DELETE FROM admins WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        await self.execute(sql, *parameters, execute=True)

    async def delete_join_requests(self, **kwargs):
        sql = "DELETE FROM join_requests WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        await self.execute(sql, *parameters, execute=True)

    async def delete_mailing(self):
        await self.execute("DELETE FROM mailing WHERE TRUE", execute=True)

    # Todo: count function

    async def count_all_users(self):
        res = {}
        all_res = await self.execute("SELECT COUNT(*) FROM users", fetchval=True)
        if all_res:
            res["all"] = all_res
        else:
            res["all"] = 0
        active_res = await self.execute(
            "SELECT COUNT(*) FROM users WHERE status='active'", fetchval=True
        )
        if active_res:
            res["active"] = active_res
        else:
            res["active"] = 0
        count_daily_users = await self.execute(
            "SELECT COUNT(*) FROM users WHERE DATE(created_at) = CURRENT_DATE;",
            fetchval=True,
        )
        if count_daily_users:
            res["daily_users"] = count_daily_users

        else:
            res["daily_users"] = 0
        count_weekly_users = await self.execute(
            """SELECT COUNT(*) FROM users WHERE created_at >= CURRENT_DATE - INTERVAL '1 week' AND created_at < CURRENT_DATE + INTERVAL '1 day';""",
            fetchval=True,
        )
        if count_weekly_users:
            res["weekly_users"] = count_weekly_users
        else:
            res["weekly_users"] = 0

        count_monthly_users = await self.execute(
            """SELECT COUNT(*) FROM users WHERE created_at >= CURRENT_DATE - INTERVAL '1 month' AND created_at < CURRENT_DATE + INTERVAL '1 day';""",
            fetchval=True,
        )
        if count_monthly_users:
            res["monthly_users"] = count_monthly_users
        else:
            res["monthly_users"] = 0
        count_unique_users = await self.execute(
            "SELECT COUNT(*) FROM users WHERE DATE(unique_at) = CURRENT_DATE;",
            fetchval=True,
        )
        if count_unique_users:
            res["unique_users"] = count_unique_users

        else:
            res["unique_users"] = 0
        return res

    async def count_language_users(self):
        result = {}
        for key in lang_file:
            result[f"{lang_file[key]['emoji']} {lang_file[key]['nativeName']}"] = (
                await self.execute(
                    "SELECT COUNT(*) FROM users WHERE lang='{}'".format(key),
                    fetchval=True,
                )
            )
        return result

    async def count_all_groups(self):
        res = {}
        all_res = await self.execute("SELECT COUNT(*) FROM groups", fetchval=True)
        if all_res:
            res["all"] = all_res
        else:
            res["all"] = 0

        active_res = await self.execute(
            "SELECT COUNT(*) FROM groups WHERE status='active'", fetchval=True
        )
        if active_res:
            res["active"] = active_res
        else:
            res["active"] = 0

        count_daily_users = await self.execute(
            "SELECT COUNT(*) FROM groups WHERE DATE(created_at) = CURRENT_DATE;",
            fetchval=True,
        )
        if count_daily_users:
            res["daily_users"] = count_daily_users
        else:
            res["daily_users"] = 0

        count_weekly_users = await self.execute(
            """SELECT COUNT(*) FROM groups WHERE created_at >= CURRENT_DATE - INTERVAL '1 week' AND created_at < CURRENT_DATE + INTERVAL '1 day';""",
            fetchval=True,
        )
        if count_weekly_users:
            res["weekly_users"] = count_weekly_users
        else:
            res["weekly_users"] = 0

        count_monthly_users = await self.execute(
            """SELECT COUNT(*) FROM groups WHERE created_at >= CURRENT_DATE - INTERVAL '1 month' AND created_at < CURRENT_DATE + INTERVAL '1 day';""",
            fetchval=True,
        )
        if count_monthly_users:
            res["monthly_users"] = count_monthly_users
        else:
            res["monthly_users"] = 0
        return res

    async def count_all_content(self):
        res = {}
        all_res = await self.execute("SELECT COUNT(*) FROM audios", fetchval=True)
        if all_res:
            res["audio"] = all_res
        else:
            res["audio"] = 0

        count_daily_audio = await self.execute(
            "SELECT COUNT(*) FROM audios WHERE DATE(created_at) = CURRENT_DATE;",
            fetchval=True,
        )
        if count_daily_audio:
            res["daily_audio"] = count_daily_audio
        else:
            res["daily_audio"] = 0

        all_res1 = await self.execute("SELECT COUNT(*) FROM medias", fetchval=True)
        if all_res1:
            res["media"] = all_res1
        else:
            res["media"] = 0

        count_daily_media = await self.execute(
            "SELECT COUNT(*) FROM medias WHERE DATE(created_at) = CURRENT_DATE;",
            fetchval=True,
        )
        if count_daily_media:
            res["daily_media"] = count_daily_media
        else:
            res["daily_media"] = 0
        return res

    async def count_ads(self):
        return await self.execute("SELECT COUNT(*) FROM ads", fetchval=True)

    # Todo: drop function

    async def drop_all_tables(self):
        await self.execute(
            "DROP TABLE IF EXISTS users, channels, join_requests;", execute=True
        )
