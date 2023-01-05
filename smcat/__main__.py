"""
Script for viewing a sitemap
"""
import sys
import logging
import click
import dateparser
import smcat
import smcat.models
import sqlalchemy.sql

LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "WARN": logging.WARNING,
    "ERROR": logging.ERROR,
    "FATAL": logging.CRITICAL,
    "CRITICAL": logging.CRITICAL,
}
LOG_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"
LOG_FORMAT = "%(asctime)s %(name)s:%(levelname)s: %(message)s"
_L = logging.getLogger("smcat")

@click.group()
@click.option(
    "-V",
    "--verbosity",
    default="INFO",
    help="Specify logging level",
    show_default=True,
)
@click.option(
    "-d",
    "--dbcnstr",
    default="sqlite:///sitemap.db",
    help="Database connection string",
    show_default=True
)
@click.pass_context
def main(ctx, verbosity, dbcnstr) -> int:
    ctx.ensure_object(dict)
    verbosity = verbosity.upper()
    logging.basicConfig(
        level=LOG_LEVELS.get(verbosity, logging.INFO),
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
    )
    if verbosity not in LOG_LEVELS.keys():
        _L.warning("%s is not a log level, set to INFO", verbosity)
    engine = None
    if dbcnstr is not None:
        engine = smcat.models.init_db(dbcnstr)
    ctx.obj['engine'] = engine

    '''tree = smcat.loadSitemap(url, engine=engine)
    if engine is not None:
        with smcat.models.get_session(engine) as session:
            for row in session.execute(sqlalchemy.sql.select(smcat.models.SitemapEntry)):
                print(row[0])
        session.close_all()
    else:
        for item in tree:
            if item.get("kind", None) is not None:
                print(f"LEAF: {item}")
    '''
    return 0

@main.command()
@click.pass_context
@click.option(
    "-u",
    "--url",
    default=None,
    help="Sitemap URL to access."
)
def load(ctx, url):
    engine = ctx.obj.get("engine", None)
    if engine is None:
        raise ValueError("Unexpected None engine.")
    if url is None:
        # Examine db to find the root
        roots = smcat.models.getSitemapRoots(engine)
        if len(roots) == 0:
            _L.error("No root URL in database and none provided.")
            return
        if len(roots) > 1:
            print("More than one root URL, specify which to use with -u <url>")
            for root in roots:
                print(root)
            return
        url = roots[0][0]
    print(f"URL = {url}")
    tree = smcat.loadSitemap(url, engine=engine)
    with smcat.models.get_session(engine) as session:
        for row in session.execute(sqlalchemy.sql.select(smcat.models.SitemapEntry)):
            print(row[0])
        session.close_all()

@main.command()
@click.pass_context
@click.option(
    "-t",
    "--tlast",
    default=None,
    help="Changes since t"
)
def recent(ctx, tlast):
    engine = ctx.obj.get("engine", None)
    if engine is None:
        raise ValueError("Unexpected None engine.")
    if tlast is None:
        most_recent = smcat.models.mostRecentEntry(engine)
        print(f"Most recent lastMod = {most_recent}")
        return
    dtlast = dateparser.parse(tlast, settings={'RETURN_AS_TIMEZONE_AWARE': True})
    for entry in smcat.models.changedSince(engine, tlast):
        print(entry)


if __name__ == "__main__":
    sys.exit(main())
