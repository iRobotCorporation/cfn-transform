from setuptools import setup

setup(
    name='cfn-transform',
    version='0.1.0',
    description='CloudFormation template transformation helper',
    py_modules=["cfn_transform"],
    entry_points={
        'console_scripts': [
            'cfn-transform = cfn_transform:module_main',
        ],
    },
    install_requires=["pyyaml"],
    author='Ben Kehoe',
    author_email='bkehoe@irobot.com',
    project_urls={
        "Source Code": "https://github.com/benkehoe/cfn-transform",
    },
    license='Apache Software License 2.0',
    classifiers=(
        'Development Status :: 2 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'License :: OSI Approved :: Apache Software License',
    ),
    keywords='aws cloudformation',
)