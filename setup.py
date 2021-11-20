from setuptools import setup

setup(
    name='anygraph',
    version='0.2.6',
    description='add any graph structure between classes with 2 simple classes',
    long_description='see <https://github.com/gemerden/anygraph>',  # after long battle to get markdown to work on PyPI
    author='Lars van Gemerden',
    author_email='gemerden@gmail.com',
    url='https://github.com/gemerden/anygraph',
    license='MIT License',
    packages=['anygraph'],
    install_requires=[],
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development',
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    python_requires='>=3.6',
    keywords='graphs trees descriptors iterators easy-to-use depth-first breadth-first dijkstra astar A*',
)
