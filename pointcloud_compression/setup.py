from setuptools import find_packages, setup

package_name = 'pointcloud_compression'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools', 'zstandard'],
    zip_safe=True,
    maintainer='you',
    maintainer_email='you@example.com',
    description='Compress/decompress PointCloud2 messages for bandwidth-limited links',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'compress_node = pointcloud_compression.compress_node:main',
            'decompress_node = pointcloud_compression.decompress_node:main',
        ],
    },
)
