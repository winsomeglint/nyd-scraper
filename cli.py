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


@cli.command()
@click.pass_context
@click.argument('target_id', required=False)
def scrape_disclosures(ctx, target_id=None):
    ctx.obj['scraper'].scrape_disclosures(target_id)


@cli.command()
@click.pass_context
def scrape_filers(ctx):
    ctx.obj['scraper'].scrape_filers()


@cli.command()
@click.pass_context
@click.argument('target_id', required=False)
def parse_disclosures(ctx, target_id=None):
    ctx.obj['parser'].parse_disclosures(target_id)


@cli.command()
@click.pass_context
def parse_filers(ctx):
    ctx.obj['parser'].parse_filers()


if __name__ == '__main__':
    cli(obj={})
