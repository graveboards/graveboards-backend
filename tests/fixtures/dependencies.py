"""
Test dependency graph visualization.

Generates and visualizes test fixture dependencies.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional

try:
    import graphviz
    HAS_GRAPHVIZ = True
except ImportError:
    HAS_GRAPHVIZ = False


class TestDependencyGraph:
    """Analyzes and visualizes test fixture dependencies."""
    
    def __init__(self, tests_dir: Path):
        self.tests_dir = tests_dir
        self.dependencies: Dict[str, List[str]] = {}
        self.reverse_deps: Dict[str, List[str]] = {}
        self.test_files: List[Path] = []
    
    def discover_tests(self) -> List[Path]:
        """Discover all test files."""
        self.test_files = list(self.tests_dir.glob("**/test_*.py"))
        return self.test_files
    
    def analyze_test_dependencies(self) -> Dict[str, List[str]]:
        """Analyze what fixtures each test depends on."""
        for test_file in self.test_files:
            test_name = str(test_file.relative_to(self.tests_dir))
            fixtures = self._extract_fixture_usage(test_file)
            self.dependencies[test_name] = fixtures
            
            for fixture in fixtures:
                if fixture not in self.reverse_deps:
                    self.reverse_deps[fixture] = []
                self.reverse_deps[fixture].append(test_name)
        
        return self.dependencies
    
    def _extract_fixture_usage(self, filepath: Path) -> List[str]:
        """Extract fixture names from test file."""
        fixtures = []
        
        with open(filepath) as f:
            content = f.read()
        
        patterns = [
            r'load_\w+\(',
            r'fixture_manager\.get_\w+\(',
            r'generate_\w+_data\(',
            r'def\s+(\w+)\([^)]*\)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            fixtures.extend(matches)
        
        seen = set()
        unique_fixtures = []
        for f in fixtures:
            if f not in seen:
                seen.add(f)
                unique_fixtures.append(f)
        
        return unique_fixtures
    
    def get_fixtures_used_in_test(self, test_file: Path) -> List[str]:
        """Get list of fixtures used in a specific test."""
        return self.dependencies.get(str(test_file.relative_to(self.tests_dir)), [])
    
    def get_tests_using_fixture(self, fixture_name: str) -> List[str]:
        """Get list of tests that use a specific fixture."""
        return self.reverse_deps.get(fixture_name, [])
    
    def generate_graph(self, output_format: str = "png") -> Optional[Path]:
        """Generate a dependency graph using graphviz."""
        if not HAS_GRAPHVIZ:
            return None
        
        dot = graphviz.Digraph(
            "test_dependencies",
            filename="test_dependencies",
            graph_attr={
                "rankdir": "TB",
                "splines": "ortho",
            },
            node_attr={
                "fontname": "Arial",
                "fontsize": "10",
            },
        )
        
        for test_name, fixtures in self.dependencies.items():
            dot.node(
                f"test_{test_name}",
                test_name,
                shape="box",
                style="rounded,filled",
                fillcolor="#e3f2fd",
            )
            
            for fixture in fixtures:
                dot.node(
                    f"fixture_{fixture}",
                    fixture,
                    shape="ellipse",
                    style="rounded,filled",
                    fillcolor="#e8f4e8",
                )
                dot.edge(f"test_{test_name}", f"fixture_{fixture}")
        
        output_dir = self.tests_dir / "fixtures"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "test_dependencies"
        
        dot.render(output_path, format=output_format, cleanup=True)
        return output_path.with_suffix(f".{output_format}")


def analyze_dependencies(tests_dir: Path = Path("tests")) -> Dict:
    """Analyze test dependencies and return summary."""
    graph = TestDependencyGraph(tests_dir)
    graph.discover_tests()
    graph.analyze_test_dependencies()
    
    summary = {
        "total_tests": len(graph.test_files),
        "total_fixture_types": len(graph.reverse_deps),
        "fixtures": list(graph.reverse_deps.keys()),
    }
    
    return summary


def print_dependency_report(graph: TestDependencyGraph):
    """Print a text-based dependency report."""
    print("\nTest Dependency Report")
    print("=" * 60)
    
    for test_name, fixtures in sorted(graph.dependencies.items()):
        print(f"\n{test_name}:")
        if fixtures:
            for fixture in fixtures:
                print(f"  └─ {fixture}")
        else:
            print("  └─ (no fixtures)")
    
    print(f"\n{'=' * 60}")
    print(f"Total tests: {len(graph.dependencies)}")
    print(f"Total fixture types: {len(graph.reverse_deps)}")


if __name__ == "__main__":
    import sys
    tests_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("tests")
    graph = TestDependencyGraph(tests_dir)
    graph.discover_tests()
    graph.analyze_test_dependencies()
    print_dependency_report(graph)
