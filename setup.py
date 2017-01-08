from setuptools import setup

setup(name="har2lilua",
      description="Convert HTTP Archive files (HAR) to LoadImpact (loadimpact.com) user scenario scripts (Lua)",
      url="http://github.com/griatch/har2lilua",
      author="Griatch",
      author_email="griatch AT gmail DOT com",
      license = "BSD",
      packages = ["har2lilua"],
      install_requires  = ["dateutils"])
