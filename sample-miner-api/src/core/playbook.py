"""Playbook management for user preferences."""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from src.models.models import PlaybookNode, PlaybookAction

logger = logging.getLogger(__name__)


class PlaybookManager:
    """Manages a user's preference playbook as structured nodes."""
    
    def __init__(self):
        self.nodes: Dict[str, PlaybookNode] = {}
        self._node_counter = 0
    
    def _generate_node_id(self) -> str:
        """Generate a unique node ID."""
        self._node_counter += 1
        return f"pref_{self._node_counter:03d}"
    
    def insert(self, content: str, category: Optional[str] = None, node_id: Optional[str] = None) -> PlaybookNode:
        """
        Insert a new preference node.
        
        Args:
            content: The preference content
            category: Optional category (e.g., 'style', 'domain', 'format')
            node_id: Optional specific node ID, otherwise auto-generated
            
        Returns:
            The created PlaybookNode
        """
        if not node_id:
            node_id = self._generate_node_id()
        
        # Check if node already exists
        if node_id in self.nodes:
            logger.warning(f"Node {node_id} already exists, updating instead of inserting")
            return self.update(node_id, content, category)
        
        now = datetime.utcnow().isoformat()
        node = PlaybookNode(
            node_id=node_id,
            content=content,
            category=category,
            created_at=now,
            updated_at=now
        )
        
        self.nodes[node_id] = node
        logger.info(f"Inserted playbook node {node_id}: {content[:50]}...")
        return node
    
    def update(self, node_id: str, content: Optional[str] = None, category: Optional[str] = None) -> Optional[PlaybookNode]:
        """
        Update an existing preference node.
        
        Args:
            node_id: The node ID to update
            content: New content (if provided)
            category: New category (if provided)
            
        Returns:
            The updated PlaybookNode, or None if not found
        """
        if node_id not in self.nodes:
            logger.warning(f"Cannot update node {node_id}: not found")
            return None
        
        node = self.nodes[node_id]
        
        if content is not None:
            node.content = content
        
        if category is not None:
            node.category = category
        
        node.updated_at = datetime.utcnow().isoformat()
        
        logger.info(f"Updated playbook node {node_id}")
        return node
    
    def delete(self, node_id: str) -> bool:
        """
        Delete a preference node.
        
        Args:
            node_id: The node ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        if node_id in self.nodes:
            del self.nodes[node_id]
            logger.info(f"Deleted playbook node {node_id}")
            return True
        else:
            logger.warning(f"Cannot delete node {node_id}: not found")
            return False
    
    def get(self, node_id: str) -> Optional[PlaybookNode]:
        """Get a specific node by ID."""
        return self.nodes.get(node_id)
    
    def get_all(self) -> List[PlaybookNode]:
        """Get all nodes as a list."""
        return list(self.nodes.values())
    
    def get_by_category(self, category: str) -> List[PlaybookNode]:
        """Get all nodes in a specific category."""
        return [node for node in self.nodes.values() if node.category == category]
    
    def apply_actions(self, actions: List[PlaybookAction]) -> List[Dict]:
        """
        Apply a list of playbook actions.
        
        Args:
            actions: List of PlaybookAction objects
            
        Returns:
            List of results for each action
        """
        results = []
        
        for action in actions:
            result = {
                "action": action.action,
                "node_id": action.node_id,
                "success": False,
                "message": ""
            }
            
            try:
                if action.action == "insert":
                    if not action.content:
                        result["message"] = "Insert action requires content"
                    else:
                        node = self.insert(
                            content=action.content,
                            category=action.category,
                            node_id=action.node_id
                        )
                        result["success"] = True
                        result["message"] = f"Inserted node {node.node_id}"
                        result["content"] = action.content
                
                elif action.action == "update":
                    node = self.update(
                        node_id=action.node_id,
                        content=action.content,
                        category=action.category
                    )
                    if node:
                        result["success"] = True
                        result["message"] = f"Updated node {action.node_id}"
                        result["content"] = node.content
                    else:
                        result["message"] = f"Node {action.node_id} not found"
                
                elif action.action == "delete":
                    success = self.delete(action.node_id)
                    result["success"] = success
                    result["message"] = f"Deleted node {action.node_id}" if success else f"Node {action.node_id} not found"
                
                else:
                    result["message"] = f"Unknown action: {action.action}"
                
            except Exception as e:
                result["message"] = f"Error: {str(e)}"
                logger.error(f"Error applying action {action.action} to node {action.node_id}: {e}")
            
            results.append(result)
        
        return results
    
    def to_context_string(self) -> str:
        """
        Convert playbook to a string for inclusion in LLM context.
        
        Returns:
            Formatted string of all preferences
        """
        if not self.nodes:
            return ""
        
        lines = ["User Preferences (Playbook):"]
        
        # Group by category
        categories = {}
        for node in self.nodes.values():
            cat = node.category or "general"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(node)
        
        # Format by category
        for category, nodes in sorted(categories.items()):
            lines.append(f"\n{category.upper()}:")
            for node in nodes:
                lines.append(f"  [{node.node_id}] {node.content}")
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict:
        """Convert playbook to dictionary for serialization."""
        return {
            node_id: {
                "node_id": node.node_id,
                "content": node.content,
                "category": node.category,
                "created_at": node.created_at,
                "updated_at": node.updated_at
            }
            for node_id, node in self.nodes.items()
        }
    
    def get_stats(self) -> Dict:
        """Get statistics about the playbook."""
        categories = {}
        for node in self.nodes.values():
            cat = node.category or "general"
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            "total_nodes": len(self.nodes),
            "categories": categories,
            "node_ids": list(self.nodes.keys())
        }
