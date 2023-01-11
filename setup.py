from setuptools import setup

VERSION = '0.0.2'
DESCRIPTION = 'Render Watcher for Katana jobs'

# Setting up
setup(
    name="RenderWatcher",
    version=VERSION,
    author="jlonghurst",
    author_email="jlonghurst@thelightersguild.com",
    description=DESCRIPTION,
    py_modules=["ui"],
    install_requires=[],
    #package_dir={'bin'},
    packages=['render_watcher'],
    classifiers=["Programming Language :: Python :: 3"],
)
