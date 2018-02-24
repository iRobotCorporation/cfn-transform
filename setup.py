from setuptools import setup

def find_version(name):
    import os.path, codecs, re
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, name), 'r') as fp:
        version_file = fp.read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

setup(
    name='cfn-transform',
    version=find_version('cfn_transform.py'),
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
        'Programming Language :: Python :: 3.5',
        'License :: OSI Approved :: Apache Software License',
    ),
    keywords='aws cloudformation',
)