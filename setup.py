import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="discord-logging",
    version="1.3.0",
    author="Watchful One",
    author_email="watchful@watchful.gr",
    description="A logging package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Watchful1/DiscordLogging",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
