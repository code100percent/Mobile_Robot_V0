#!/usr/bin/env python3
"""Offline structural checks; does not import ROS or execute launch files."""
import ast
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ('mobile_robot_driver', 'robot_description', 'sensor_bringup')


def main():
    for package in PACKAGES:
        folder = ROOT / package
        manifest = ET.parse(folder / 'package.xml').getroot()
        assert manifest.findtext('name') == package, folder
        assert (folder / 'resource' / package).is_file(), folder
        for path in folder.rglob('*.py'):
            ast.parse(path.read_text(), filename=str(path))
    robot = ET.parse(ROOT / 'robot_description/urdf/mobile_robot.urdf').getroot()
    links = [link.attrib['name'] for link in robot.findall('link')]
    assert len(links) == len(set(links)), 'Duplicate URDF links'
    parents = {}
    for joint in robot.findall('joint'):
        parent = joint.find('parent').attrib['link']
        child = joint.find('child').attrib['link']
        assert parent in links and child in links, joint.attrib['name']
        assert child not in parents, f'Multiple parents for {child}'
        parents[child] = parent
    roots = set(links) - parents.keys()
    assert len(roots) == 1, f'Expected one URDF root, got {roots}'
    for link in links:
        visited = set()
        while link in parents:
            assert link not in visited, 'URDF cycle'
            visited.add(link)
            link = parents[link]
        assert link in roots, 'Disconnected URDF'
    print('Package manifests, Python syntax, and URDF tree checks passed.')


if __name__ == '__main__':
    main()
