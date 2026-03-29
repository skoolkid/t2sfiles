from setuptools import Extension, setup

setup(
    ext_modules=[
        Extension("libz80diff", ["libz80diff.c"], optional=True),
    ]
)
