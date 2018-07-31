from setuptools import setup

setup_kwargs = dict(
    name='nav',
    version='5.2.0',
    description='Conveniently make requests to Microsoft Dynamics NAV Web Services',
    packages=['nav', 'nav.wrappers'],
    include_package_data=True,
    author='Jacob Magnusson',
    author_email='m@jacobian.se',
    url='https://github.com/jmagnusson/nav',
    license='BSD',
    platforms='any',
    install_requires=[
        'lxml',
        'requests-ntlm',
        'zeep>=3.0.0',
    ],
    extras_require={
        'cli': [
            'argh',
            'ipython',
        ],
        'test': {
            'coverage>=4.2',
            'flake8>=3.0.4',
            'pytest>=3.0.3',
            'responses>=0.5.1',
        },
    },
    entry_points={
        'console_scripts': [
            'nav = nav.__main__:main',
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)

if __name__ == '__main__':
    setup(**setup_kwargs)
