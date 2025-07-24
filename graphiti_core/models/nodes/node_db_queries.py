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

from typing import Any


def EPISODIC_NODE_SAVE(_provider: str) -> str:
    return """
        MERGE (n:Episodic {uuid: $uuid})
        SET
            n.name = $name,
            n.group_id = $group_id,
            n.source_description = $source_description,
            n.source = $source,
            n.content = $content,
            n.entity_edges = $entity_edges,
            n.created_at = $created_at,
            n.valid_at = $valid_at
        RETURN n.uuid AS uuid
    """


def EPISODIC_NODE_SAVE_BULK(provider: str) -> str:
    if provider == 'kuzu':
        return """
            UNWIND $episodes AS episode
            MERGE (n:Episodic {uuid: episode.uuid})
            SET
                n.name = episode.name,
                n.group_id = episode.group_id,
                n.source_description = episode.source_description,  
                n.source = episode.source,
                n.content = episode.content,
                n.entity_edges = episode.entity_edges,
                n.created_at = episode.created_at,
                n.valid_at = episode.valid_at
            RETURN n.uuid AS uuid
        """

    return """
        UNWIND $episodes AS episode
        MERGE (n:Episodic {uuid: episode.uuid})
        SET n = {uuid: episode.uuid, name: episode.name, group_id: episode.group_id,
            source_description: episode.source_description, source: episode.source,
            content: episode.content, entity_edges: episode.entity_edges,
            created_at: episode.created_at, valid_at: episode.valid_at}
        RETURN n.uuid AS uuid
    """


def EPISODIC_NODE_RETURN(_provider: str) -> str:
    return """
        e.content AS content,
        e.created_at AS created_at,
        e.valid_at AS valid_at,
        e.uuid AS uuid,
        e.name AS name,
        e.group_id AS group_id,
        e.source_description AS source_description,
        e.source AS source,
        e.entity_edges AS entity_edges
    """


def ENTITY_NODE_SAVE(provider: str) -> str:
    if provider == 'kuzu':
        return """
            MERGE (n:Entity {uuid: $uuid})
            SET
                n.labels = $labels,
                n.name = $name,
                n.name_embedding = $name_embedding,
                n.group_id = $group_id,
                n.summary = $summary,
                n.created_at = $created_at
            WITH n
            RETURN n.uuid AS uuid
        """

    return """
        MERGE (n:Entity {uuid: $entity_data.uuid})
        SET n:$($labels)
        SET n = $entity_data
        WITH n CALL db.create.setNodeVectorProperty(n, "name_embedding", $entity_data.name_embedding)
        RETURN n.uuid AS uuid
    """


def ENTITY_NODE_SAVE_BULK(nodes, provider: str) -> str | list[Any]:
    if provider == 'kuzu':
        return """
            UNWIND $nodes AS node
            MERGE (n:Entity {uuid: node.uuid})
            SET
                n.labels = node.labels,
                n.name = node.name,
                n.name_embedding = node.name_embedding,
                n.group_id = node.group_id,
                n.summary = node.summary,
                n.created_at = node.created_at
            RETURN n.uuid AS uuid
        """

    if provider == 'falkordb':
        queries = []
        for node in nodes:
            for label in node['labels']:
                queries.append(
                    (
                        f"""
                        UNWIND $nodes AS node
                        MERGE (n:Entity {{uuid: node.uuid}})
                        SET n:{label}
                        SET n = node
                        WITH n, node
                        SET n.name_embedding = vecf32(node.name_embedding)
                        RETURN n.uuid AS uuid
                        """,
                        {'nodes': [node]},
                    )
                )
        return queries

    return """
        UNWIND $nodes AS node
        MERGE (n:Entity {uuid: node.uuid})
        SET n:$(node.labels)
        SET n = node
        WITH n, node CALL db.create.setNodeVectorProperty(n, "name_embedding", node.name_embedding)
        RETURN n.uuid AS uuid
    """


def ENTITY_NODE_RETURN(provider: str) -> str:
    if provider == 'kuzu':
        return """
            n as attributes,
            n.labels as labels
        """

    return """
        properties(n) AS attributes,
        labels(n) AS labels
    """


def COMMUNITY_NODE_SAVE(provider: str) -> str:
    if provider == 'kuzu':
        return """
            MERGE (n:Community {uuid: $uuid})
            SET
                n.name = $name,
                n.name_embedding = $name_embedding,
                n.group_id = $group_id,
                n.summary = $summary,
                n.created_at = $created_at
            WITH n
            RETURN n.uuid AS uuid
        """

    return """
        MERGE (n:Community {uuid: $uuid})
        SET n = {uuid: $uuid, name: $name, group_id: $group_id, summary: $summary, created_at: $created_at}
        WITH n CALL db.create.setNodeVectorProperty(n, "name_embedding", $name_embedding)
        RETURN n.uuid AS uuid
    """


def COMMUNITY_NODE_RETURN(_provider: str) -> str:
    return """
        c.uuid As uuid,
        c.name AS name,
        c.name_embedding AS name_embedding,
        c.group_id AS group_id,
        c.summary AS summary,
        c.created_at AS created_at
    """
