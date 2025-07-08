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

import os
from datetime import datetime
from uuid import uuid4

import pytest

from graphiti_core.driver.driver import GraphDriver
from graphiti_core.driver.kuzu_driver import KuzuDriver
from graphiti_core.nodes import (
    CommunityNode,
    EntityNode,
    EpisodeType,
    EpisodicNode,
)

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


group_id = f'test_group_{str(uuid4())}'


@pytest.fixture
def sample_entity_node():
    return EntityNode(
        uuid=str(uuid4()),
        name='Test Entity',
        group_id=group_id,
        labels=[],
        name_embedding=[0.5] * 1024,
        summary='Entity Summary',
    )


@pytest.fixture
def sample_episodic_node():
    return EpisodicNode(
        uuid=str(uuid4()),
        name='Episode 1',
        group_id=group_id,
        source=EpisodeType.text,
        source_description='Test source',
        content='Some content here',
        valid_at=datetime.now(),
    )


@pytest.fixture
def sample_community_node():
    return CommunityNode(
        uuid=str(uuid4()),
        name='Community A',
        name_embedding=[0.5] * 1024,
        group_id=group_id,
        summary='Community summary',
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'driver',
    drivers,
    ids=drivers,
)
async def test_entity_node(sample_entity_node, driver):
    driver = get_driver(driver)
    uuid = sample_entity_node.uuid

    node_count = await get_node_count(driver, uuid)
    assert node_count == 0

    await sample_entity_node.save(driver)

    node_count = await get_node_count(driver, uuid)
    assert node_count == 1

    retrieved = await EntityNode.get_by_uuid(driver, sample_entity_node.uuid)
    assert retrieved.uuid == sample_entity_node.uuid
    assert retrieved.name == 'Test Entity'
    assert retrieved.group_id == group_id

    retrieved = await EntityNode.get_by_uuids(driver, [sample_entity_node.uuid])
    assert retrieved[0].uuid == sample_entity_node.uuid
    assert retrieved[0].name == 'Test Entity'
    assert retrieved[0].group_id == group_id

    retrieved = await EntityNode.get_by_group_ids(driver, [group_id], limit=2)
    assert len(retrieved) == 1
    assert retrieved[0].uuid == sample_entity_node.uuid
    assert retrieved[0].name == 'Test Entity'
    assert retrieved[0].group_id == group_id

    await sample_entity_node.load_name_embedding(driver)
    assert sample_entity_node.name_embedding == [0.5] * 1024

    await sample_entity_node.delete(driver)

    node_count = await get_node_count(driver, uuid)
    assert node_count == 0

    await driver.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'driver',
    drivers,
    ids=drivers,
)
async def test_community_node(sample_community_node, driver):
    driver = get_driver(driver)
    uuid = sample_community_node.uuid

    node_count = await get_node_count(driver, uuid)
    assert node_count == 0

    await sample_community_node.save(driver)

    node_count = await get_node_count(driver, uuid)
    assert node_count == 1

    retrieved = await CommunityNode.get_by_uuid(driver, sample_community_node.uuid)
    assert retrieved.uuid == sample_community_node.uuid
    assert retrieved.name == 'Community A'
    assert retrieved.group_id == group_id
    assert retrieved.summary == 'Community summary'

    retrieved = await CommunityNode.get_by_uuids(driver, [sample_community_node.uuid])
    assert retrieved[0].uuid == sample_community_node.uuid
    assert retrieved[0].name == 'Community A'
    assert retrieved[0].group_id == group_id
    assert retrieved[0].summary == 'Community summary'

    retrieved = await CommunityNode.get_by_group_ids(driver, [group_id], limit=2)
    assert len(retrieved) == 1
    assert retrieved[0].uuid == sample_community_node.uuid
    assert retrieved[0].name == 'Community A'
    assert retrieved[0].group_id == group_id

    await sample_community_node.delete(driver)

    node_count = await get_node_count(driver, uuid)
    assert node_count == 0

    await driver.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'driver',
    drivers,
    ids=drivers,
)
async def test_episodic_node(sample_episodic_node, driver):
    driver = get_driver(driver)
    uuid = sample_episodic_node.uuid

    node_count = await get_node_count(driver, uuid)
    assert node_count == 0

    await sample_episodic_node.save(driver)

    node_count = await get_node_count(driver, uuid)
    assert node_count == 1

    retrieved = await EpisodicNode.get_by_uuid(driver, sample_episodic_node.uuid)
    assert retrieved.uuid == sample_episodic_node.uuid
    assert retrieved.name == 'Episode 1'
    assert retrieved.group_id == group_id
    assert retrieved.source == EpisodeType.text
    assert retrieved.source_description == 'Test source'
    assert retrieved.content == 'Some content here'
    assert retrieved.valid_at == sample_episodic_node.valid_at

    retrieved = await EpisodicNode.get_by_uuids(driver, [sample_episodic_node.uuid])
    assert retrieved[0].uuid == sample_episodic_node.uuid
    assert retrieved[0].name == 'Episode 1'
    assert retrieved[0].group_id == group_id
    assert retrieved[0].source == EpisodeType.text
    assert retrieved[0].source_description == 'Test source'
    assert retrieved[0].content == 'Some content here'
    assert retrieved[0].valid_at == sample_episodic_node.valid_at

    retrieved = await EpisodicNode.get_by_group_ids(driver, [group_id], limit=2)
    assert len(retrieved) == 1
    assert retrieved[0].uuid == sample_episodic_node.uuid
    assert retrieved[0].name == 'Episode 1'
    assert retrieved[0].group_id == group_id
    assert retrieved[0].source == EpisodeType.text
    assert retrieved[0].source_description == 'Test source'
    assert retrieved[0].content == 'Some content here'
    assert retrieved[0].valid_at == sample_episodic_node.valid_at

    await sample_episodic_node.delete(driver)

    node_count = await get_node_count(driver, uuid)
    assert node_count == 0

    await driver.close()


async def get_node_count(driver: GraphDriver, uuid: str):
    result, _, _ = await driver.execute_query(
        """
        MATCH (n {uuid: $uuid})
        RETURN COUNT(n) as count
        """,
        uuid=uuid,
    )
    return int(result[0]['count'])
