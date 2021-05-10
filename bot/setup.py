from setuptools import setup

setup(
    name='bot',
    version='0.0.2',
    description='A module-extensible message bot',
    author='Nathan Latchaw',
    author_email='natelatchaw@gmail.com',
    license='Creative Commons',
    packages=['bot', 'bot.configuration', 'bot.static'],
    url='not available',
    install_requires=[
        'discord.py',
    ],
    classifiers=[
        'Development Status :: Alpha',
        'Intended Audience :: Hobbyist',
        'Operating System :: Agnostic',
        'Programming Language :: Python :: 3.9',
    ],
)