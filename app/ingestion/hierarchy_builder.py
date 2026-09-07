from .models import StructureNode


class HierarchyBuilder:
    """
    Build a hierarchical document tree from flat structure nodes.

    The input nodes must already contain their inferred hierarchy level.

    Example:

        level 1: 1
        level 2: 1.1
        level 3: 1.1.1
        level 2: 1.2
        level 1: 2

    becomes:

        1
        ├── 1.1
        │   └── 1.1.1
        └── 1.2

        2

    This class does NOT detect headings or infer document structure.
    """

    def build(
        self,
        nodes: list[StructureNode],
    ) -> list[StructureNode]:

        if not nodes:
            return []

        roots: list[StructureNode] = []

        # stack[level - 1] = most recent node at that level
        stack: list[StructureNode] = []

        for node in nodes:

            level = node.level

            if level <= 0:
                level = 1
                node.level = level

            # Remove nodes at the same or deeper level.
            while len(stack) >= level:
                stack.pop()

            # No parent -> root node
            if not stack:
                roots.append(node)

            else:
                parent = stack[-1]
                parent.children.append(node)

            stack.append(node)

        return roots