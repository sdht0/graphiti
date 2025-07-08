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
import os
import sys
from datetime import datetime, timezone

import pytest
from dotenv import load_dotenv

from graphiti_core.driver.driver import GraphDriver
from graphiti_core.driver.kuzu_driver import KuzuDriver
from graphiti_core.edges import EntityEdge, EpisodicEdge
from graphiti_core.embedder.openai import OpenAIEmbedder
from graphiti_core.graphiti import Graphiti
from graphiti_core.helpers import semaphore_gather
from graphiti_core.nodes import EntityNode, EpisodeType, EpisodicNode
from graphiti_core.search.search_filters import ComparisonOperator, DateFilter, SearchFilters
from graphiti_core.search.search_helpers import search_results_to_context_string
from graphiti_core.utils.datetime_utils import utc_now

pytestmark = pytest.mark.integration

pytest_plugins = ('pytest_asyncio',)

load_dotenv()

try:
    from graphiti_core.driver.neo4j_driver import Neo4jDriver

    HAS_NEO4J = True
except ImportError:
    HAS_NEO4J = False

try:
    from graphiti_core.driver.falkordb_driver import FalkorDriver

    HAS_FALKORDB = True
except ImportError:
    HAS_FALKORDB = False

NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'test')

FALKORDB_HOST = os.getenv('FALKORDB_HOST', 'localhost')
FALKORDB_PORT = os.getenv('FALKORDB_PORT', '6379')
FALKORDB_USER = os.getenv('FALKORDB_USER', None)
FALKORDB_PASSWORD = os.getenv('FALKORDB_PASSWORD', None)


def get_driver(driver_name: str) -> GraphDriver:
    if driver_name == 'kuzu':
        return KuzuDriver()
    elif driver_name == 'neo4j':
        return Neo4jDriver(
            uri=NEO4J_URI,
            user=NEO4J_USER,
            password=NEO4J_PASSWORD,
        )
    elif driver_name == 'falkordb':
        return FalkorDriver(
            host=FALKORDB_HOST,
            port=int(FALKORDB_PORT),
            username=FALKORDB_USER,
            password=FALKORDB_PASSWORD,
        )
    else:
        raise ValueError(f'Driver {driver_name} not available')


drivers: list[str] = ['kuzu']
if HAS_NEO4J:
    drivers.append('neo4j')
if HAS_FALKORDB:
    drivers.append('falkordb')


def setup_logging():
    # Create a logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # Set the logging level to INFO

    # Create console handler and set level to INFO
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Add formatter to console handler
    console_handler.setFormatter(formatter)

    # Add console handler to logger
    logger.addHandler(console_handler)

    return logger


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'driver',
    drivers,
    ids=drivers,
)
async def test_graphiti_init(driver):
    logger = setup_logging()
    graphiti = Graphiti(graph_driver=get_driver(driver))
    search_filter = SearchFilters(
        created_at=[[DateFilter(date=utc_now(), comparison_operator=ComparisonOperator.less_than)]]
    )

    results = await graphiti.search_(query='Who is Tania?', search_filter=search_filter)

    pretty_results = search_results_to_context_string(results)

    logger.info(pretty_results)

    await graphiti.close()
