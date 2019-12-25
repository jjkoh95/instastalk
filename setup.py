from setuptools import setup
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    readme = f.read()

setup(
    name='instastalk',
    packages=['instastalk'],
    version='0.1.15',
    license='MIT',
    description='Download your instacrush posts',
    author='jjkoh95',
    author_email='jjkoh95@gmail.com',
    url='https://github.com/jjkoh95/instastalk',
    keywords=['instagram', 'scrape'],
    install_requires=[
        'beautifulsoup4',
        'requests',
    ],
    long_description=readme,
    long_description_content_type='text/markdown',
    classifiers=[
        # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
        'Development Status :: 3 - Alpha',
        # Define that your audience are developers
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
    ],
)
