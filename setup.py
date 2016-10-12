from setuptools import setup

setup_kwargs = dict(
    name='nav-requests',
    version='1.0.0',
    description='Make Microsoft Dynamics NAV Web Services requests',
    packages=['nav_requests'],
    include_package_data=True,
    author='Jacob Magnusson',
    author_email='m@jacobian.se',
    url='https://github.com/jmagnusson/nav-requests',
    license='BSD',
    platforms='any',
    install_requires=[
        'argh',
        'lxml',
        'requests',
        'requests-ntlm',
    ],
    extras_require={
        'test': {
            'coverage>=4.2',
            'flake8>=3.0.4',
            'pytest>=3.0.3',
        },
    },
    entry_points={
        'console_scripts': [
            'navrequest = nav_requests:main',
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
    ],
)

if __name__ == '__main__':
    setup(**setup_kwargs)
