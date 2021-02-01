from setuptools import (
    setup,
    find_packages
)

about = {}
with open("mock_op/__about__.py") as fp:
    exec(fp.read(), about)

with open("README.md", "r") as fp:
    long_description = fp.read()

setup(name='mock-op',
      version=about["__version__"],
      description=about["__summary__"],
      long_description=long_description,
      long_description_content_type="text/markdown",
      author="Zachary Cutlip",
      author_email="uid000@gmail.com",
      url="TBD",
      license="MIT",
      packages=find_packages(),
      entry_points={},
      python_requires='>=3.7',
      install_requires=[],
      package_data={'mock_op': ['config/*']},
      )
