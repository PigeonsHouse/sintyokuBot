import psycopg2

with psycopg2.connect('postgresql://admin:admin@localhost:15432/admin') as conn:
    with conn.cursor() as cur:
        cur.execute("CREATE SCHEMA progress_app")
        cur.execute("CREATE TABLE progress_app.user( id bigint NOT NULL, user_name text NOT NULL, task_ids integer[], UNIQUE(id) );")
        cur.execute("CREATE TABLE progress_app.task( id serial NOT NULL, task_name text NOT NULL, user_id bigserial NOT NULL, duration interval, UNIQUE(id) );")
        cur.execute("CREATE TABLE progress_app.guild( id bigint NOT NULL, guild_name text NOT NULL, user_ids bigint[], notify_channel bigint, UNIQUE(id) );")
    conn.commit()
