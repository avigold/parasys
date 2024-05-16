from setuptools import setup, find_packages


extras = {
    'windows': ['windows-curses']  # required for curses support on Windows
}

setup(
    name='parasys',
    version='0.2.0',
    author='Avram Score',
    author_email='ascore@gmail.com',
    description='A platform-agnostic command-line tool for system monitoring.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/avigold/parasys',
    packages=find_packages(),
    install_requires=[
        'psutil',
        'asciimatics'
    ],
    extras_require=extras,
    entry_points={
        'console_scripts': [
            'parasys=parasys.monitor:main',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: System :: Monitoring',
    ],
    python_requires='>=3.6'
)
