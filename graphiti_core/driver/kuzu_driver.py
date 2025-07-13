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

from graphiti_core.driver.driver import GraphDriver, GraphDriverSession
from graphiti_core.models.edges.edge_db_queries import KUZU_EDGE_SCHEMA
from graphiti_core.models.nodes.node_db_queries import KUZU_NODE_SCHEMA

logger = logging.getLogger(__name__)


class KuzuDriver(GraphDriver):
    provider: str = 'kuzu'

    def __init__(
        self,
        db: str = ':memory:',
        max_concurrent_queries: int = 4,
    ):
        super().__init__()
        self.db = kuzu.Database(db)

        conn = kuzu.Connection(self.db)
        conn.execute(KUZU_NODE_SCHEMA)
        conn.execute(KUZU_EDGE_SCHEMA)
        conn.close()

        self.client = kuzu.AsyncConnection(self.db, max_concurrent_queries=max_concurrent_queries)

    async def execute_query(
        self, cypher_query_: str, **kwargs: Any
    ) -> tuple[list[dict[str, Any]] | list[list[dict[str, Any]]], None, None]:
        params = {k: v for k, v in kwargs.items() if v is not None}
        params.pop('database_', None)
        params.pop('routing_', None)

        print('kuzu: query = ', cypher_query_)
        print(
            'kuzu: params = ', {k: (v[:5] if isinstance(v, list) else v) for k, v in params.items()}
        )

        results = await self.client.execute(cypher_query_, parameters=params)

        if isinstance(results, list):
            dict_results = [list(result.rows_as_dict()) for result in results]
        else:
            dict_results = list(results.rows_as_dict())
        return dict_results, None, None  # type: ignore

    async def print_graph(self):
        res = await self.execute_query('MATCH (n) RETURN n')
        print("Nodes:")
        for r in res:
            print("  ", r)
        res = await self.execute_query('MATCH (n)-[r]->(m) RETURN r')
        print("Edges:")
        for r in res:
            print("  ", r)

    def session(self, _database: str) -> GraphDriverSession:
        return KuzuDriverSession(self)

    async def close(self):
        self.client.close()

    def delete_all_indexes(self, database_: str):
        pass


class KuzuDriverSession(GraphDriverSession):
    def __init__(self, driver: KuzuDriver):
        self.driver = driver

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
                await self.driver.execute_query(cypher, **params)
        else:
            await self.driver.execute_query(query, **kwargs)
        return None
