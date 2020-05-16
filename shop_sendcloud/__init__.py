"""
See PEP 386 (https://www.python.org/dev/peps/pep-0386/)

Release logic:
 1. Increase version number (change __version__ below).
 2. Check that all changes have been documented in CHANGELOG.md.
 3. In setup.py, assure that `classifiers` and `install_requires` reflect the latest versions.
 4. git add shop_sendcloud/__init__.py CHANGELOG.md setup.py
 5. git commit -m 'Bump to {new version}'
 6. git tag {new version}
 7. git push --tags
 8. python setup.py sdist
 9. twine upload dist/djangoshop-sendcloud-{new version}.tar.gz
"""
__version__ = '1.2.1'
