import re
import sys
import click
import requests
import logging

from os import path
from hashlib import md5

from classes.parsetool import DisclosuresParser
from classes.scrapetool import DisclosuresScraper

logging.basicConfig(level=logging.INFO)


@click.group()
@click.pass_context
def cli(ctx):
    ctx.obj['scraper'] = DisclosuresScraper()
    ctx.obj['parser'] = DisclosuresParser()
    pass


@click.command()
@click.pass_context
def scrape_disclosures(ctx):
    ctx.obj['scraper'].scrape_disclosures()


@click.command()
@click.pass_context
def scrape_filer_ids(ctx):
    ctx.obj['scraper'].scrape_filer_ids()


@click.command()
@click.pass_context
def parse_disclosures(ctx):
    ctx.obj['parser'].parse_disclosures()


@click.command()
@click.pass_context
def parse_filer_ids(ctx):
    ctx.obj['parser'].parse_filer_ids()


cli.add_command(scrape_disclosures)
cli.add_command(scrape_filer_ids)
cli.add_command(parse_disclosures)
cli.add_command(parse_filer_ids)


if __name__ == '__main__':
    cli(obj={})
