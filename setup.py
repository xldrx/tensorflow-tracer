from setuptools import setup
import os

with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "README.md"), "r") as fp:
    long_description = fp.read()

setup(
    name='tensorflow-tracer',
    version='1.0.1',
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
    install_requires=['bokeh>=1.0', "flask", "jinja2", "tensorflow>=1.8", "six", "gevent"],
    package_data={'tftracer': ['resources/*/*']},
)
