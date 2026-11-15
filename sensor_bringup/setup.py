from glob import glob
import os

from setuptools import setup

package_name = 'sensor_bringup'

setup(
    name=package_name,
    version='0.0.1',
    packages=[],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob(os.path.join('launch', '*.launch.py'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='sehaj',
    maintainer_email='sehajthewarrior@gmail.com',
    description='Combined camera and Unitree LiDAR bringup.',
    license='Apache-2.0',
)
