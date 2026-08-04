from setuptools import setup
import os
from glob import glob

package_name = 'bota_node'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'config'), glob('config/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Valentin Yuryev',
    maintainer_email='valentin.yuryev@epfl.ch',
    description='ROS2 node for Bota Systems force/torque sensors via bota-driver.',
    license='MIT',
    entry_points={
        'console_scripts': [
            'bota_node = bota_node.bota_node:main',
        ],
    },
)
