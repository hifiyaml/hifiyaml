from setuptools import setup, find_packages

setup(
    name="hifiyaml",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[],       # add dependencies if needed
    description="High-fidelity YAML processing with original structure and format preserved (such as comments, anchors, aliases, etc)"
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Guoqing Ge",
    url="https://github.com/hifiyaml/hifiyaml",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.9',
)
