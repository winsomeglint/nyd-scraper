from setuptools import setup, find_packages

setup(
    name='nyd-scraper',
    version='1.0',
    packages=find_packages(),
    scripts=['cli.py'],
    install_requires=['requests', 'lxml', 'click'],
    author='Lion Summerbell',
    description='Scraper to download filers and disclosures from elections.ny.gov',
    license='ISC',
    keywords='ny state elections',
    url='https://github.com/anabase/ny_disclosures',
    entry_ponts={
        'console_scripts': [
            'nyd-scraper = cli',
        ]
    }
)
