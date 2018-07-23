import re
import sys
import click
import requests
import logging

from os import path
from hashlib import md5

from app.parser import DisclosuresParser
from app.scraper import DisclosuresScraper

logging.basicConfig(level=logging.INFO)


@click.group()
@click.pass_context
def cli(ctx):
    ctx.obj['scraper'] = DisclosuresScraper()
    ctx.obj['parser'] = DisclosuresParser()


@click.command()
@click.pass_context
def scrape_disclosures(ctx):
    ctx.obj['scraper'].scrape_disclosures()


@click.command()
@click.pass_context
def scrape_filers(ctx):
    ctx.obj['scraper'].scrape_filers()


@click.command()
@click.pass_context
def parse_disclosures(ctx):
    ctx.obj['parser'].parse_disclosures()


@click.command()
@click.pass_context
def parse_filers(ctx):
    ctx.obj['parser'].parse_filers()


cli.add_command(scrape_disclosures)
cli.add_command(scrape_filers)
cli.add_command(parse_disclosures)
cli.add_command(parse_filers)


if __name__ == '__main__':
    cli(obj={})
