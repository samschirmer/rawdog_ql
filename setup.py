from setuptools import setup, find_packages

setup(
    name="rawdog_ql",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[],
    author="Sam Schirmer",
    author_email="samschirmer@gmail.com",
    description="A package for asynchronous database operations using raw SQL",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/samschirmer/rawdog_ql",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: OS Independent",
    ],
    license="GPL-2.0",
    python_requires='>=3.6',
    extras_require={
        'dev': ['python-dotenv', 'asyncio'],
    },
)
