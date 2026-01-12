"""
V0.40: LIFE-GRAPH ENDPOINT (Stub)

3D/2D visualization of knowledge graph showing:
- Classes as nodes
- Projects as nodes
- Study Packs as nodes
- Artifacts as nodes
- Relationships as edges (contains, references, requires, related_to)

Currently a MINIMAL MVP - feature-flagged OFF by default.

Future work: Real-time graph UI, 3D visualization, graph algorithms, etc.
"""

from fastapi import APIRouter, Depends, HTTPException, Cookie
from sqlalchemy.orm import Session
from typing import Optional, List, Dict
from datetime import datetime

from marcus_app.core.database import get_db
from marcus_app.core.models import (
    LifeGraphNode, LifeGraphEdge,
    Class, Project, StudyPack, Artifact,
    SystemConfig, Mission, MissionBox, MissionArtifact
)
from marcus_app.core.schemas import LifeGraphNodeResponse, LifeGraphEdgeResponse, LifeGraphResponse


router = APIRouter(prefix="/api", tags=["life-graph"])


def require_auth(session_token: Optional[str] = Cookie(None, alias="marcus_session")):
    """Require authentication."""
    from marcus_app.backend.api import auth_service
    if not session_token or not auth_service.validate_session(session_token):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return session_token


def is_life_graph_enabled(db: Session) -> bool:
    """Check if Life-Graph feature is enabled."""
    config = db.query(SystemConfig).filter(
        SystemConfig.key == 'enable_life_view'
    ).first()
    return config and config.value == 'true'


# ============================================================================
# LIFE-GRAPH ENDPOINTS
# ============================================================================

@router.get("/life-graph", response_model=LifeGraphResponse)
async def get_life_graph(
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """
    Retrieve the complete life-graph of knowledge.
    
    Returns nodes (classes, projects, study packs, artifacts) and edges (relationships).
    
    Currently a STUB - returns minimal MVP with basic structure.
    """
    # Check if enabled
    if not is_life_graph_enabled(db):
        raise HTTPException(
            status_code=423,
            detail="Life-Graph feature is currently disabled. Contact admin to enable."
        )
    
    # Get all nodes
    nodes = db.query(LifeGraphNode).all()
    edges = db.query(LifeGraphEdge).all()
    
    # If no data yet, generate from existing entities
    if not nodes:
        nodes = _generate_initial_graph(db)
    
    # Convert to response models
    node_responses = [
        LifeGraphNodeResponse(
            id=n.id,
            node_type=n.node_type,
            entity_id=n.entity_id,
            label=n.label,
            description=n.description or "",
            x=n.x or 0,
            y=n.y or 0,
            z=n.z or 0
        )
        for n in nodes
    ]
    
    edge_responses = [
        LifeGraphEdgeResponse(
            id=e.id,
            source_node_id=e.source_node_id,
            target_node_id=e.target_node_id,
            edge_type=e.edge_type
        )
        for e in edges
    ]
    
    return LifeGraphResponse(
        nodes=node_responses,
        edges=edge_responses,
        node_count=len(node_responses),
        edge_count=len(edge_responses),
        generated_at=datetime.utcnow()
    )


def _generate_initial_graph(db: Session) -> List[LifeGraphNode]:
    """
    Generate initial graph from existing entities.

    Creates nodes for:
    - Classes (highest level)
    - Projects (user's dev projects)
    - Study Packs (learning artifacts)
    - Artifacts (vault files, notes, etc)
    - Missions (v0.44-final: workflow missions)
    - MissionBoxes (v0.44-final: box operations)
    - MissionArtifacts (v0.44-final: mission outputs)

    And edges for relationships between them.
    """
    nodes = []
    edges = []
    next_node_id = 1
    next_edge_id = 1
    node_map = {}  # Track entity_type:entity_id -> node_id

    # 1. Add Class nodes
    classes = db.query(Class).limit(20).all()  # Limit to avoid huge graph
    for cls in classes:
        node = LifeGraphNode(
            id=next_node_id,
            node_type='class',
            entity_id=cls.id,
            label=cls.name,
            description=f"Class: {cls.number if hasattr(cls, 'number') else 'Unknown'}",
            x=0, y=0, z=0
        )
        nodes.append(node)
        node_map[f'class:{cls.id}'] = next_node_id
        next_node_id += 1

    # 2. Add Project nodes
    projects = db.query(Project).limit(20).all()
    for proj in projects:
        node = LifeGraphNode(
            id=next_node_id,
            node_type='project',
            entity_id=proj.id,
            label=proj.name,
            description=f"Project: {proj.description[:50] if proj.description else 'No description'}",
            x=10, y=0, z=0
        )
        nodes.append(node)
        node_map[f'project:{proj.id}'] = next_node_id
        next_node_id += 1

    # 3. Add StudyPack nodes
    study_packs = db.query(StudyPack).limit(20).all()
    for pack in study_packs:
        node = LifeGraphNode(
            id=next_node_id,
            node_type='study_pack',
            entity_id=pack.id,
            label=pack.name,
            description=f"Study Pack: {pack.description[:50] if pack.description else 'No description'}",
            x=5, y=10, z=0
        )
        nodes.append(node)
        node_map[f'study_pack:{pack.id}'] = next_node_id
        next_node_id += 1

    # 4. Add Artifact nodes
    artifacts = db.query(Artifact).limit(20).all()
    for artifact in artifacts:
        node = LifeGraphNode(
            id=next_node_id,
            node_type='artifact',
            entity_id=artifact.id,
            label=artifact.name,
            description=f"Artifact: {artifact.artifact_type}",
            x=7, y=5, z=0
        )
        nodes.append(node)
        node_map[f'artifact:{artifact.id}'] = next_node_id
        next_node_id += 1

    # 5. Add Mission nodes (v0.44-final)
    missions = db.query(Mission).limit(20).all()
    for mission in missions:
        node = LifeGraphNode(
            id=next_node_id,
            node_type='mission',
            entity_id=mission.id,
            label=mission.name,
            description=f"Mission: {mission.mission_type} ({mission.state})",
            x=-5, y=5, z=5
        )
        nodes.append(node)
        node_map[f'mission:{mission.id}'] = next_node_id

        # Create edge: class -> mission (if mission has class_id)
        if mission.class_id and f'class:{mission.class_id}' in node_map:
            edge = LifeGraphEdge(
                id=next_edge_id,
                source_node_id=node_map[f'class:{mission.class_id}'],
                target_node_id=next_node_id,
                edge_type='contains'
            )
            edges.append(edge)
            next_edge_id += 1

        next_node_id += 1

    # 6. Add MissionBox nodes (v0.44-final)
    mission_boxes = db.query(MissionBox).limit(50).all()
    for box in mission_boxes:
        node = LifeGraphNode(
            id=next_node_id,
            node_type='mission_box',
            entity_id=box.id,
            label=f"{box.box_type}",
            description=f"Box: {box.box_type} ({box.state})",
            x=-3, y=7, z=5
        )
        nodes.append(node)
        node_map[f'mission_box:{box.id}'] = next_node_id

        # Create edge: mission -> box
        if f'mission:{box.mission_id}' in node_map:
            edge = LifeGraphEdge(
                id=next_edge_id,
                source_node_id=node_map[f'mission:{box.mission_id}'],
                target_node_id=next_node_id,
                edge_type='contains'
            )
            edges.append(edge)
            next_edge_id += 1

        next_node_id += 1

    # 7. Add MissionArtifact nodes (v0.44-final)
    mission_artifacts = db.query(MissionArtifact).limit(50).all()
    for ma in mission_artifacts:
        node = LifeGraphNode(
            id=next_node_id,
            node_type='mission_artifact',
            entity_id=ma.id,
            label=ma.title[:30],
            description=f"Artifact: {ma.artifact_type}",
            x=-1, y=9, z=5
        )
        nodes.append(node)
        node_map[f'mission_artifact:{ma.id}'] = next_node_id

        # Create edge: box -> artifact
        if ma.box_id and f'mission_box:{ma.box_id}' in node_map:
            edge = LifeGraphEdge(
                id=next_edge_id,
                source_node_id=node_map[f'mission_box:{ma.box_id}'],
                target_node_id=next_node_id,
                edge_type='contains'
            )
            edges.append(edge)
            next_edge_id += 1

        next_node_id += 1

    # Save all nodes and edges
    for node in nodes:
        db.add(node)
    for edge in edges:
        db.add(edge)
    db.commit()

    return nodes


@router.get("/life-graph/stats")
async def get_life_graph_stats(
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """Get statistics about the knowledge graph."""
    if not is_life_graph_enabled(db):
        raise HTTPException(status_code=423, detail="Life-Graph feature is disabled")
    
    node_count = db.query(LifeGraphNode).count()
    edge_count = db.query(LifeGraphEdge).count()
    
    node_types = {}
    for node in db.query(LifeGraphNode.node_type).distinct():
        count = db.query(LifeGraphNode).filter(LifeGraphNode.node_type == node[0]).count()
        node_types[node[0]] = count
    
    return {
        "total_nodes": node_count,
        "total_edges": edge_count,
        "node_types": node_types,
        "enabled": True
    }


@router.post("/life-graph/enable")
async def enable_life_graph(
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """Enable the Life-Graph feature."""
    config = db.query(SystemConfig).filter(
        SystemConfig.key == 'enable_life_view'
    ).first()
    
    if not config:
        config = SystemConfig(key='enable_life_view', value='true')
        db.add(config)
    else:
        config.value = 'true'
    
    db.commit()
    
    return {"status": "life_graph_enabled"}


@router.post("/life-graph/disable")
async def disable_life_graph(
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """Disable the Life-Graph feature."""
    config = db.query(SystemConfig).filter(
        SystemConfig.key == 'enable_life_view'
    ).first()
    
    if config:
        config.value = 'false'
        db.commit()
    
    return {"status": "life_graph_disabled"}


@router.get("/life-graph/nodes")
async def get_graph_nodes(
    node_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """Get specific graph nodes by type or entity."""
    if not is_life_graph_enabled(db):
        raise HTTPException(status_code=423, detail="Life-Graph feature is disabled")
    
    query = db.query(LifeGraphNode)
    
    if node_type:
        query = query.filter(LifeGraphNode.node_type == node_type)
    
    if entity_id:
        query = query.filter(LifeGraphNode.entity_id == entity_id)
    
    nodes = query.limit(100).all()
    
    return [
        {
            "id": n.id,
            "node_type": n.node_type,
            "entity_id": n.entity_id,
            "label": n.label,
            "description": n.description or ""
        }
        for n in nodes
    ]


@router.get("/life-graph/edges")
async def get_graph_edges(
    source_id: Optional[int] = None,
    target_id: Optional[int] = None,
    edge_type: Optional[str] = None,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """Get specific graph edges by source, target, or type."""
    if not is_life_graph_enabled(db):
        raise HTTPException(status_code=423, detail="Life-Graph feature is disabled")
    
    query = db.query(LifeGraphEdge)
    
    if source_id:
        query = query.filter(LifeGraphEdge.source_node_id == source_id)
    
    if target_id:
        query = query.filter(LifeGraphEdge.target_node_id == target_id)
    
    if edge_type:
        query = query.filter(LifeGraphEdge.edge_type == edge_type)
    
    edges = query.limit(100).all()
    
    return [
        {
            "id": e.id,
            "source_node_id": e.source_node_id,
            "target_node_id": e.target_node_id,
            "edge_type": e.edge_type
        }
        for e in edges
    ]


@router.post("/life-graph/add-edge")
async def add_graph_edge(
    source_id: int,
    target_id: int,
    edge_type: str,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """
    Manually add an edge to the knowledge graph.
    
    Valid edge types:
    - contains: Source contains target
    - references: Source references target
    - requires: Source requires target
    - related_to: Source is related to target
    """
    if not is_life_graph_enabled(db):
        raise HTTPException(status_code=423, detail="Life-Graph feature is disabled")
    
    valid_types = ['contains', 'references', 'requires', 'related_to']
    if edge_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid edge_type. Must be one of: {', '.join(valid_types)}")
    
    # Check that nodes exist
    source = db.query(LifeGraphNode).filter(LifeGraphNode.id == source_id).first()
    target = db.query(LifeGraphNode).filter(LifeGraphNode.id == target_id).first()
    
    if not source or not target:
        raise HTTPException(status_code=404, detail="Source or target node not found")
    
    # Check for duplicate
    existing = db.query(LifeGraphEdge).filter(
        LifeGraphEdge.source_node_id == source_id,
        LifeGraphEdge.target_node_id == target_id,
        LifeGraphEdge.edge_type == edge_type
    ).first()
    
    if existing:
        raise HTTPException(status_code=409, detail="Edge already exists")
    
    edge = LifeGraphEdge(
        source_node_id=source_id,
        target_node_id=target_id,
        edge_type=edge_type,
        created_at=datetime.utcnow()
    )
    
    db.add(edge)
    db.commit()
    
    return {
        "id": edge.id,
        "source_node_id": source_id,
        "target_node_id": target_id,
        "edge_type": edge_type,
        "status": "edge_created"
    }
