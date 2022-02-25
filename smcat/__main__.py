"""
Script for viewing a sitemap
"""
import sys
import logging
import click
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

@click.command()
@click.argument("url")
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
    default=None,
    help="Database connection string",
    show_default=True
)
def main(url, verbosity, dbcnstr) -> int:
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
    tree = smcat.loadSitemap(url, engine=engine)
    if engine is not None:
        with smcat.models.get_session(engine) as session:
            for row in session.execute(sqlalchemy.sql.select(smcat.models.SitemapEntry)):
                print(row[0])
        session.close_all()
    else:
        for item in tree:
            if item.get("kind", None) is not None:
                print(f"LEAF: {item}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
