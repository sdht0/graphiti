"""
Copyright 2024, Zep Software, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import logging
from typing import Any

import kuzu
from typing_extensions import LiteralString

from graphiti_core.driver.driver import GraphDriver, GraphDriverSession
from graphiti_core.helpers import DEFAULT_DATABASE

logger = logging.getLogger(__name__)

class KuzuDriverSession(GraphDriverSession):
    def __init__(self, connection: kuzu.AsyncConnection):
        self.connection = connection

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        # No cleanup needed for Kuzu, but method must exist
        pass

    async def close(self):
        # No explicit close needed for Kuzu, but method must exist
        pass

    async def execute_write(self, func, *args, **kwargs):
        # Directly await the provided async function with `self` as the transaction/session
        return await func(self, *args, **kwargs)

    async def run(self, query: str | list, **kwargs: Any) -> Any:
        if isinstance(query, list):
            for cypher, params in query:
                await self.connection.execute(str(cypher), params)
        else:
            params = dict(kwargs)
            await self.connection.execute(str(query), params)
        return None


class KuzuDriver(GraphDriver):
    provider: str = 'kuzu'

    def __init__(
        self,
        db: str = ':memory:',
        max_concurrent_queries: int = 4,
    ):
        super().__init__()
        self.db = kuzu.Database(db)
        self.client = kuzu.AsyncConnection(self.db, max_concurrent_queries=max_concurrent_queries)

    async def execute_query(self, cypher_query_: LiteralString, **kwargs: Any) -> kuzu.QueryResult | list[kuzu.QueryResult]:
        params = kwargs.pop('params', None)
        result = await self.client.execute(cypher_query_, parameters=params)

        return result

    def session(self, _database: str) -> GraphDriverSession:
        return KuzuDriverSession(self.client)

    async def close(self):
        self.client.close()

    def delete_all_indexes(
        self, database_: str = DEFAULT_DATABASE
    ):
        pass
