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

KUZU_EDGE_SCHEMA = """
    CREATE REL TABLE IF NOT EXISTS MENTIONS(
        FROM Episodic TO Entity,
        uuid STRING PRIMARY KEY,
        group_id STRING,
        created_at TIMESTAMP,
        fact_embedding FLOAT[]
    );
    CREATE REL TABLE IF NOT EXISTS RELATES_TO(
        FROM Entity TO Entity,
        uuid STRING PRIMARY KEY,
        group_id STRING,
        name STRING,
        fact STRING,
        fact_embedding FLOAT[],
        episodes STRING[],
        created_at TIMESTAMP,
        expired_at TIMESTAMP,
        valid_at TIMESTAMP,
        invalid_at TIMESTAMP
    );
    CREATE REL TABLE IF NOT EXISTS HAS_MEMBER(
        FROM Community TO Entity,
        FROM Community TO Community,
        uuid STRING PRIMARY KEY,
        group_id STRING,
        created_at TIMESTAMP
    );
"""

def EPISODIC_EDGE_SAVE(provider: str) -> str:
    if provider == 'kuzu':
        return """
            MATCH (episode:Episodic {uuid: $episode_uuid}) 
            MATCH (node:Entity {uuid: $entity_uuid}) 
            MERGE (episode)-[r:MENTIONS {uuid: $uuid}]->(node)
            SET
                r.uuid = $uuid,
                r.group_id = $group_id,
                r.created_at = $created_at
            RETURN r.uuid AS uuid
        """

    return """
        MATCH (episode:Episodic {uuid: $episode_uuid}) 
        MATCH (node:Entity {uuid: $entity_uuid}) 
        MERGE (episode)-[r:MENTIONS {uuid: $uuid}]->(node)
        SET r = {uuid: $uuid, group_id: $group_id, created_at: $created_at}
        RETURN r.uuid AS uuid
    """

EPISODIC_EDGE_SAVE_BULK = """
    UNWIND $episodic_edges AS edge
    MATCH (episode:Episodic {uuid: edge.source_node_uuid}) 
    MATCH (node:Entity {uuid: edge.target_node_uuid}) 
    MERGE (episode)-[r:MENTIONS {uuid: edge.uuid}]->(node)
    SET r = {uuid: edge.uuid, group_id: edge.group_id, created_at: edge.created_at}
    RETURN r.uuid AS uuid
"""

def ENTITY_EDGE_RETURN(provider: str) -> str:
    if provider == 'kuzu':
        return """
            e.uuid AS uuid,
            n.uuid AS source_node_uuid,
            m.uuid AS target_node_uuid,
            e.created_at AS created_at,
            e.name AS name,
            e.group_id AS group_id,
            e.fact AS fact,
            e.episodes AS episodes,
            e.expired_at AS expired_at,
            e.valid_at AS valid_at,
            e.invalid_at AS invalid_at,
            e AS attributes
        """

    return """
        e.uuid AS uuid,
        startNode(e).uuid AS source_node_uuid,
        endNode(e).uuid AS target_node_uuid,
        e.created_at AS created_at,
        e.name AS name,
        e.group_id AS group_id,
        e.fact AS fact,
        e.episodes AS episodes,
        e.expired_at AS expired_at,
        e.valid_at AS valid_at,
        e.invalid_at AS invalid_at,
        properties(e) AS attributes
    """

def ENTITY_EDGE_RETURN_COLLECT(provider: str) -> str:
    if provider == 'kuzu':
        return """
            collect({
                uuid: e.uuid,
                source_node_uuid: startNode(e).uuid,
                target_node_uuid: endNode(e).uuid,
                created_at: e.created_at,
                name: e.name,
                group_id: e.group_id,
                fact: e.fact,
                episodes: e.episodes,
                expired_at: e.expired_at,
                valid_at: e.valid_at,
                invalid_at: e.invalid_at,
                attributes: properties(e)
            })
        """

    return """
        e.uuid AS uuid,
        startNode(e).uuid AS source_node_uuid,
        endNode(e).uuid AS target_node_uuid,
        e.created_at AS created_at,
        e.name AS name,
        e.group_id AS group_id,
        e.fact AS fact,
        e.episodes AS episodes,
        e.expired_at AS expired_at,
        e.valid_at AS valid_at,
        e.invalid_at AS invalid_at,
        properties(e) AS attributes
    """

def ENTITY_EDGE_SAVE(provider: str) -> str:
    if provider == 'kuzu':
        return """
            MATCH (source:Entity {uuid: $source_uuid})
            MATCH (target:Entity {uuid: $target_uuid})
            MERGE (source)-[r:RELATES_TO {uuid: $uuid}]->(target)
            SET
                r.name = $name,
                r.group_id = $group_id,
                r.fact = $fact,
                r.fact_embedding = $fact_embedding,
                r.episodes = $episodes,
                r.created_at = $created_at,
                r.expired_at = $expired_at,
                r.valid_at = $valid_at,
                r.invalid_at = $invalid_at
            RETURN r.uuid AS uuid
        """

    return """
        MATCH (source:Entity {uuid: $edge_data.source_uuid})
        MATCH (target:Entity {uuid: $edge_data.target_uuid})
        MERGE (source)-[r:RELATES_TO {uuid: $edge_data.uuid}]->(target)
        SET r = $edge_data
        WITH r CALL db.create.setRelationshipVectorProperty(r, "fact_embedding", $edge_data.fact_embedding)
        RETURN r.uuid AS uuid
    """

ENTITY_EDGE_SAVE_BULK = """
    UNWIND $entity_edges AS edge
    MATCH (source:Entity {uuid: edge.source_node_uuid}) 
    MATCH (target:Entity {uuid: edge.target_node_uuid}) 
    MERGE (source)-[r:RELATES_TO {uuid: edge.uuid}]->(target)
    SET r = edge
    WITH r, edge CALL db.create.setRelationshipVectorProperty(r, "fact_embedding", edge.fact_embedding)
    RETURN edge.uuid AS uuid
"""

def COMMUNITY_EDGE_RETURN(_provider: str) -> str:
    return """
        e.uuid As uuid,
        e.group_id AS group_id,
        n.uuid AS source_node_uuid, 
        m.uuid AS target_node_uuid, 
        e.created_at AS created_at
    """

def COMMUNITY_EDGE_SAVE(provider: str) -> str:
    if provider == 'kuzu':
        return """
            MATCH (community:Community {uuid: $community_uuid}) 
            MATCH (node:Entity {uuid: $entity_uuid}) 
            MERGE (community)-[r:HAS_MEMBER {uuid: $uuid}]->(node)
            SET
                r.uuid = $uuid,
                r.group_id = $group_id,
                r.created_at = $created_at
            RETURN r.uuid AS uuid
            UNION
            MATCH (community:Community {uuid: $community_uuid}) 
            MATCH (node:Community {uuid: $entity_uuid}) 
            MERGE (community)-[r:HAS_MEMBER {uuid: $uuid}]->(node)
            SET
                r.uuid = $uuid,
                r.group_id = $group_id,
                r.created_at = $created_at
            RETURN r.uuid AS uuid
        """

    return """
        MATCH (community:Community {uuid: $community_uuid}) 
        MATCH (node:Entity | Community {uuid: $entity_uuid}) 
        MERGE (community)-[r:HAS_MEMBER {uuid: $uuid}]->(node)
        SET r = {uuid: $uuid, group_id: $group_id, created_at: $created_at}
        RETURN r.uuid AS uuid
    """
