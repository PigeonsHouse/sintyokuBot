import psycopg2

with psycopg2.connect('postgresql://admin:admin@localhost:15432/admin') as conn:
    with conn.cursor() as cur:
        cur.execute("CREATE SCHEMA progress_app")
        cur.execute("CREATE TABLE progress_app.user( id bigserial NOT NULL, user_name text NOT NULL, task_ids integer[], UNIQUE(id) );")
        cur.execute("CREATE TABLE progress_app.task( id serial NOT NULL, task_name text NOT NULL, user_id bigserial NOT NULL, duration interval, UNIQUE(id) );")
    conn.commit()