from setuptools import setup

setup(
    name='instastalk',
    packages=['instastalk'],
    version='0.1.1',
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
    classifiers=[
        # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
        'Development Status :: 3 - Alpha',
        # Define that your audience are developers
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)
