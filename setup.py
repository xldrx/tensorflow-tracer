from setuptools import setup
import os
from tftracer.version import __version__
with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "README.md"), "r") as fp:
    long_description = fp.read()

with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "requirements.txt"), "r") as fp:
    requirements = fp.read().split("\n")


setup(
    name='tensorflow-tracer',
    version=__version__,
    packages=['tftracer'],
    url='https://github.com/xldrx/tensorflow-tracer',
    license='Apache-2.0',
    author='Sayed Hadi Hashemi',
    author_email='SayedHadiHashemi@gmail.com',
    description='Runtime Tracing Library for TensorFlow',
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3 :: Only",
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': [
            'tftracer=tftracer.__main__:main',
        ],
    },
    install_requires=requirements,
    package_data={'tftracer': ['resources/*/*']},
)
