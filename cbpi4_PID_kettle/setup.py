from setuptools import setup, find_packages

setup(
    name='cbpi4_PID_kettle',
    version='0.0.1',
    description='CraftBeerPi4 Plugin for PID controlled kettle',
    author='Your Name',
    author_email='your.email@example.com',
    url='https://github.com/yourusername/cbpi4_PID_kettle',
    include_package_data=True,
    package_data={
        '': ['*.txt', '*.rst', '*.yaml'],
        'cbpi4_PID_kettle': ['*', '*.txt', '*.rst', '*.yaml'],
    },
    packages=find_packages(),
    install_requires=['cbpi4'],
    entry_points={'cbpi4': ['cbpi4_PID_kettle = cbpi4_PID_kettle:setup']},
)
