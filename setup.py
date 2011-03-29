from setuptools import setup, find_packages
import os

version = '1.0a1'

setup(name='plone.bbb_testing',
      version=version,
      description="ZopeTestCase and PortalTestCase backward-compatible "
          "helper classes for plone.testing",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      classifiers=[
        "Programming Language :: Python",
        ],
      keywords='',
      author='Godefroid Chapelle',
      author_email='gotcha@bubblenet.be',
      url='http://svn.plone.org/svn/plone/plone.bbb_testing/trunk',
      license='GPL',
      packages=find_packages('src'),
      package_dir={'': 'src'},
      namespace_packages=['plone'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'plone.testing',
      ],
      )
