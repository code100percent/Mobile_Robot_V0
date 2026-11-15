from setuptools import find_packages, setup
import os
from glob import glob
package_name = 'mobile_robot_driver'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),

        (os.path.join('share', package_name, 'config'),
            glob(os.path.join('config', '*.yaml'))),

        # Install launch files
        (os.path.join('share', package_name, 'launch'),
            glob(os.path.join('launch', '*.launch.py'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='sehaj',
    maintainer_email='sehajthewarrior@gmail.com',
    description='Differential-drive wheel encoder odometry and base driver launch.',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'encoder_odometry = mobile_robot_driver.encoder_odometry:main',
        ],
    },
)
