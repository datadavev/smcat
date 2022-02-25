import typing
import logging
import datetime
import json
import sqlalchemy
import sqlmodel

_L = logging.getLogger("models.sitemap")


class SitemapBase(sqlmodel.SQLModel):

    loc: str = sqlmodel.Field(
        primary_key=True,
        nullable=False,
        description="loc for a single url entry in a sitemap",
    )

    t_created: datetime.datetime = sqlmodel.Field(
        default=datetime.datetime.now(tz=datetime.timezone.utc),
        nullable=False,
        sa_column=sqlalchemy.Column(
            sqlalchemy.DateTime(timezone=True),
            doc="Timestamp for when this entry was created",
        )
    )

    t_updated: datetime.datetime = sqlmodel.Field(
        default=datetime.datetime.now(tz=datetime.timezone.utc),
        nullable=False,
        sa_column=sqlalchemy.Column(
            sqlalchemy.DateTime(timezone=True),
            onupdate=datetime.datetime.now(tz=datetime.timezone.utc),
            doc="Timestamp for when this entry was modified",
        )
    )

    lastmod: datetime.datetime = sqlmodel.Field(
        nullable=True,
        sa_column=sqlalchemy.Column(
            sqlalchemy.DateTime(timezone=True),
            default=None,
            doc="Date time lastmod entry from loc, if present",
        )
    )

    properties: dict = sqlmodel.Field(
        sa_column=sqlalchemy.Column(
            sqlalchemy.JSON,
            doc="Properties in addition to the standard sitemap elements",
        )
    )

    def asJsonDict(self) -> typing.Dict:
        res = {
            "loc": self.loc,
            "lastmod": self.lastmod
            if self.lastmod is None
            else self.lastmod.isoformat(),
            "t_created": self.t_created.isoformat(),
            "t_updated": self.t_updated.isoformat(),
            "properties": self.properties,
        }
        return res

    def __str__(self):
        return json.dumps(self.asJsonDict(), indent=2)

    def __repr__(self):
        return json.dumps(self.asJsonDict(), indent=0, separators=(":", ","))


class SitemapIndex(SitemapBase, table=True):

    source: typing.Optional[str] = sqlmodel.Field(
        default=None, foreign_key="sitemapindex.loc"
    )


class SitemapEntry(SitemapBase, table=True):

    priority: float = sqlmodel.Field(
        default=None, nullable=True, description="loc priority entry"
    )

    source: typing.Optional[str] = sqlmodel.Field(
        default=None, foreign_key="sitemapindex.loc"
    )

    changefreq: str = sqlmodel.Field(
        default=None,
        nullable=True,
        description="changefreq from loc, the frequency of change: always, hourly, daily, weekly, monthly, yearly, never"
    )

    def asJsonDict(self) -> typing.Dict:
        res = super().asJsonDict()
        res["source"] = self.source
        res["priority"] = self.priority
        res["changefreq"] = self.changefreq
        return res

