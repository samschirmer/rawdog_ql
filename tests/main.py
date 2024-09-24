import os
from os.path import join, dirname
import asyncio
import rawdog_ql as rawdog
from rawdog_ql import select_one, select_all, cud_query, insert_transaction
import aioodbc
import asyncpg
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)


async def init_sqlsrv():
    url = os.getenv("SQLSRV_URL")
    db = os.getenv("SQLSRV_DB")
    usr = os.getenv("SQLSRV_USER")
    pwd = os.getenv("SQLSRV_PASS")
    port = os.getenv("SQLSRV_PORT")
    host_os = os.getenv("HOST_OS")
    conn_str = None
    if host_os == 'windows' or host_os == 'mac':
        conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={url};DATABASE={db};UID={usr};PWD={pwd}'
    elif host_os == 'linux':
        conn_str = f"DRIVER=FreeTDS;SERVER={url};PORT={port};DATABASE={db};UID={usr};PWD={pwd};TDS_Version=8.0"

    recycle_secs = 1800
    return await aioodbc.create_pool(dsn=conn_str, autocommit=True, pool_recycle=recycle_secs)


async def init_pg():
    url = os.getenv("PG_URL")
    db = os.getenv("PG_DB")
    usr = os.getenv("PG_USER")
    pwd = os.getenv("PG_PASS")
    port = os.getenv("PG_PORT")
    conn_str = f"postgresql://{usr}:{pwd}@{url}:{port}/{db}"
    return await asyncpg.create_pool(conn_str)


async def test_pg(pg_db):
    async with pg_db.acquire() as conn:
        try:
            # Ensure connection is alive
            result = await conn.fetchval("SELECT 1;")
            print(f"Postgres connection alive, query result: {result}")

            query = "select email, active from users where id = $1"
            params = (1,)
            user = await rawdog.select_one(conn, query, params)
            print(f"Postgres user: {user}")
            active = user['active']

            query = "select email from users where id > $1 and id < $2"
            params = (1, 10)
            users = await rawdog.select_all(conn, query, params)
            print(f"Postgres users: {users}")

            # Update and revert active status
            query = "update users set active = $1 where id = $2"
            params = (not active, 1)
            await rawdog.cud_query(conn, query, params)
            query = "select active from users where id = $1"
            user = await rawdog.select_one(conn, query, (1,))
            print(f"Active status: {user['active']}; reverting...")
            await rawdog.cud_query(conn, "update users set active = $1 where id = $2", (active, 1))
            user = await rawdog.select_one(conn, "select active from users where id = $1", (1,))
            print(f"Active back to: {user['active']}")
        except Exception as e:
            print(f"Postgres Error: {e}")


async def test_sqlsrv(sqlsrv_db):
    async with sqlsrv_db.acquire() as conn:
        try:
            async with conn.cursor() as cursor:
                query = "select UserID, Email from tblusers where userid = ?"
                params = (1,)
                await cursor.execute(query, params)
                user = await cursor.fetchone()
                columns = [column[0] for column in cursor.description]
                result = {columns[i]: value for i, value in enumerate(user)}
                print(f"SQL Server user: {result}")
        except Exception as e:
            print(f"SQL Server Error: {e}")


async def main():
    sqlsrv_db = await init_sqlsrv()
    pg_db = await init_pg()

    await test_sqlsrv(sqlsrv_db)
    await test_pg(pg_db)

    sqlsrv_db.close()
    await sqlsrv_db.wait_closed()
    await pg_db.close()


if __name__ == "__main__":
    asyncio.run(main())