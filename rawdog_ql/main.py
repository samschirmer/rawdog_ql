try:
    import aioodbc
except ImportError:
    aioodbc = None

try:
    import asyncpg
except ImportError:
    asyncpg = None


def is_mssql(db):
    if aioodbc is None:
        return False
    return isinstance(db, aioodbc.Connection)


def is_postgres(db):
    if asyncpg is None:
        return False
    return isinstance(db, asyncpg.Connection)


async def _execute_query(db, query, params):
    if is_mssql(db):
        async with db.cursor() as cursor:
            await cursor.execute(query, params)
            return cursor
    elif is_postgres(db):
        query_lower = query.strip().lower()
        if query_lower.startswith("select"):
            return await db.fetch(query, *params) if params else await db.fetch(query)
        else:
            return await db.execute(query, *params)


async def _fetch_results(cursor_or_result):
    if hasattr(cursor_or_result, 'fetchall'):  # MS SQL Server
        return await cursor_or_result.fetchall()
    else:  # PostgreSQL (asyncpg returns result directly)
        return cursor_or_result


async def select_one(db, query, params):
    try:
        cursor_or_result = await _execute_query(db, query, params)
        if is_mssql(db):
            result = await cursor_or_result.fetchone()
            if result:
                columns = [column[0] for column in cursor_or_result.description]
                return {columns[i]: value for i, value in enumerate(result)}
            else:
                return None
        elif is_postgres(db):
            return dict(cursor_or_result[0]) if cursor_or_result else None
    except Exception as e:
        raise e


async def select_all(db, query, params):
    records = []
    try:
        cursor_or_result = await _execute_query(db, query, params)
        if not cursor_or_result:
            return records

        if is_mssql(db):
            columns = [column[0] for column in cursor_or_result.description]
            records = [{columns[i]: value for i, value in enumerate(row)} for row in await cursor_or_result.fetchall()]
        elif is_postgres(db):
            records = [dict(row) for row in cursor_or_result]

        return records
    except Exception as e:
        raise e


async def cud_query(db, query, params):
    try:
        cursor_or_result = await _execute_query(db, query, params)
        if is_mssql(db):
            await db.commit()
            return cursor_or_result.rowcount if cursor_or_result else None
        elif is_postgres(db):
            return cursor_or_result
    except Exception as e:
        if is_mssql(db):
            await db.rollback()
        raise e


async def execute_procedure(db, query, params):
    return await cud_query(db, query, params)


async def insert_returning_new_id(db, query, params, pg_id_col="id"):
    if is_mssql(db):
        try:
            insert_query = f"{query}; SELECT SCOPE_IDENTITY();"
            cursor_or_result = await _execute_query(db, insert_query, params)
            result = await _fetch_results(cursor_or_result)
            await db.commit()
            return result[0][0] if result else None
        except Exception as e:
            await db.rollback()
            raise e

    if is_postgres(db):
        try:
            insert_query = f"{query} RETURNING {pg_id_col};"
            cursor_or_result = await _execute_query(db, insert_query, params)
            result = await _fetch_results(cursor_or_result)
            return result[0][pg_id_col] if result else None
        except Exception as e:
            raise e


async def insert_transaction(db, txn_queries):
    async def _execute_transaction():
        for query_set in txn_queries:
            curr_query = query_set['query']
            curr_params = query_set['params']
            err_msg = query_set.get('msg', 'No error message provided')
            try:
                await _execute_query(db, curr_query, curr_params)
            except Exception as e:
                print(f'Problem with db transaction: {err_msg} {e} / {curr_query} / {curr_params}')
                raise e

    try:
        if is_mssql(db):
            await _execute_transaction()
            await db.commit()
        elif is_postgres(db):
            async with db.transaction():
                await _execute_transaction()
    except Exception as e:
        if is_mssql(db):
            await db.rollback()
        raise e
