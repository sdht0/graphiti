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

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from graphiti_core.driver.kuzu_driver import KuzuDriver
from graphiti_core.nodes import (
    CommunityNode,
    EntityNode,
    EpisodeType,
    EpisodicNode,
)


@pytest.fixture
def sample_entity_node():
    return EntityNode(
        uuid=str(uuid4()),
        name='Test Entity',
        group_id='test_group',
        labels=[],
        name_embedding=[0.5] * 1024,
        summary='Entity Summary',
    )


@pytest.fixture
def sample_episodic_node():
    return EpisodicNode(
        uuid=str(uuid4()),
        name='Episode 1',
        group_id='test_group',
        source=EpisodeType.text,
        source_description='Test source',
        content='Some content here',
        valid_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_community_node():
    return CommunityNode(
        uuid=str(uuid4()),
        name='Community A',
        name_embedding=[0.5] * 1024,
        group_id='test_group',
        summary='Community summary',
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "driver",
    [
        KuzuDriver(),
    ],
)
async def test_entity_node_save_get_and_delete(sample_entity_node, driver):
    await sample_entity_node.save(driver)

    retrieved = await EntityNode.get_by_uuid(driver, sample_entity_node.uuid)
    assert retrieved.uuid == sample_entity_node.uuid
    assert retrieved.name == 'Test Entity'
    assert retrieved.group_id == 'test_group'

    retrieved = await EntityNode.get_by_uuids(driver, [sample_entity_node.uuid])
    assert retrieved[0].uuid == sample_entity_node.uuid
    assert retrieved[0].name == 'Test Entity'
    assert retrieved[0].group_id == 'test_group'

    name_embedding = await sample_entity_node.load_name_embedding(driver)
    assert name_embedding == [0.5] * 1024

    await sample_entity_node.delete(driver)

    await driver.close()


@pytest.mark.asyncio
async def test_community_node_save_get_and_delete(sample_community_node):
    kuzu_driver = KuzuDriver()

    await sample_community_node.save(kuzu_driver)

    retrieved = await CommunityNode.get_by_uuid(kuzu_driver, sample_community_node.uuid)
    assert retrieved.uuid == sample_community_node.uuid
    assert retrieved.name == 'Community A'
    assert retrieved.group_id == 'test_group'
    assert retrieved.summary == 'Community summary'

    await sample_community_node.delete(kuzu_driver)

    await kuzu_driver.close()


@pytest.mark.asyncio
async def test_episodic_node_save_get_and_delete(sample_episodic_node):
    kuzu_driver = KuzuDriver()

    await sample_episodic_node.save(kuzu_driver)

    retrieved = await EpisodicNode.get_by_uuid(kuzu_driver, sample_episodic_node.uuid)
    assert retrieved.uuid == sample_episodic_node.uuid
    assert retrieved.name == 'Episode 1'
    assert retrieved.group_id == 'test_group'
    assert retrieved.source == EpisodeType.text
    assert retrieved.source_description == 'Test source'
    assert retrieved.content == 'Some content here'

    await sample_episodic_node.delete(kuzu_driver)

    await kuzu_driver.close()
