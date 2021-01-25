#!/usr/bin/env python3

from distutils.core import setup
import sys


if __name__ == '__main__':
	
	setup(name='n4d',
		version='0.908',
		description='N4d',
		long_description="""""",
		author='Hector Garcia Huerta',
		author_email='hectorgh@gmail.com',
		maintainer='Hector Garcia Huerta',
		maintainer_email='hectorgh@gmail.com',
		keywords=['n4d','xmlrpc'],
		url='http://github.com/lliurex/n4d',
		license='GPL',
		platforms='UNIX',
		packages = ['n4d.server','n4d.responses', 'n4d.utils'],
		package_dir = {'n4d.server':'server','n4d.responses':'responses','n4d.utils':'utils'},
		data_files = [],
		classifiers=[
			'Development Status :: 4 - Beta',
			'Environment :: Console'
			'Intended Audience :: End Users',
			'License :: OSI Approved :: GNU General Public License v3',
			'Operating System :: POSIX',
			'Programming Language :: Python',
			'Topic :: Software',
			'Topic :: Install apps',
			],
	)
