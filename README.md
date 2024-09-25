# RawdogQL: Async Database Utilities

This package provides utility functions for asynchronous database operations with either MS SQL Server (aioodbc) or PostgreSQL (asyncpg). 

It does not manage your connections. It does not return objects. It does not abstract anything, really.

Pass an async db object, a raw SQL query, and your params. 
It will perform the query and either return a dict of the results or raise an error. 

## Installation

Install the package using pip:

```
pip install rawdog_ql
```

**Note**: Either aioodbc OR asyncpg is required to be installed.

## Usage

Here's a quick example of how to use the package:


### Select
```python
from rawdog_ql import select_one_by_query

# Assuming you have an async database connection "db"
async def get_user():
    result = await select_one_by_query(db, "SELECT id, name FROM users WHERE id = ?", (1,))
    print(results)
    # {"id": 123, "name": "Alec Holland"}
    
```

### Insert Returning ID + Transactions
```python
from rawdog_ql import insert_transaction, insert_returning_new_id

async def create_album():
    try:
        # Assuming you have an aioodbc or pyodbc database connection "sqlsrv_db"
        new_id = await insert_returning_new_id(sqlsrv_db, "INSERT INTO albums (name, band) VALUES (?, ?)", ("Dopesmoker", "Sleep"))

        # Assuming you have an asyncpg database connection "pg_db"
        new_id = await insert_returning_new_id(pg_db, "INSERT INTO albums (name, band) VALUES (?, ?)", ("Dopesmoker", "Sleep"), "album_id")

        err_msg = "inserting new song for album"
        txn_queries = [
            {"query": "INSERT INTO songs (album_id, name) VALUES (?, ?)", "params": (new_id, "Dopesmoker"), "msg": err_msg},
            {"query": "INSERT INTO songs (album_id, name) VALUES (?, ?)", "params": (new_id, "Holy Mountain"), "msg": err_msg},
            {"query": "INSERT INTO songs (album_id, name) VALUES (?, ?)", "params": (new_id, "Sonic Titan"), "msg": err_msg}
        ]
        await insert_transaction(sqlsrv_db, txn_queries)
    except Exception as e:
        print(e)
```

## License

This project is licensed under the GPL-2.0.