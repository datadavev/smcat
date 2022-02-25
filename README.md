# smcat
Sitemap cat

```
smcat "https://www.bco-dmo.org/sitemap.xml" -d "sqlite:///bco-dmo.db"
```

```
sqlite> .schema
CREATE TABLE sitemapindex (
	t_created DATETIME,
	t_updated DATETIME,
	lastmod DATETIME,
	properties JSON,
	loc VARCHAR NOT NULL,
	source VARCHAR,
	PRIMARY KEY (loc),
	FOREIGN KEY(source) REFERENCES sitemapindex (loc)
);
CREATE TABLE sitemapentry (
	t_created DATETIME,
	t_updated DATETIME,
	lastmod DATETIME,
	properties JSON,
	loc VARCHAR NOT NULL,
	priority FLOAT,
	source VARCHAR,
	changefreq VARCHAR,
	PRIMARY KEY (loc),
	FOREIGN KEY(source) REFERENCES sitemapindex (loc)
);

sqlite> select lastmod, source, loc from sitemapindex;
2022-01-03 17:00:00.000000|https://www.bco-dmo.org/sitemap.xml|http://www.bco-dmo.org/sitemap.xml?page=1
2022-01-03 17:00:00.000000|https://www.bco-dmo.org/sitemap.xml|http://www.bco-dmo.org/sitemap.xml?page=2

sqlite> select lastmod, priority, loc from sitemapentry where source='http://www.bco-dmo.org/sitemap.xml?page=2' limit 5;
2012-11-05 17:06:00.000000||http://www.bco-dmo.org/award/54613
2016-08-20 03:10:00.000000|0.9|http://www.bco-dmo.org/dataset/546131
2012-11-05 17:06:00.000000||http://www.bco-dmo.org/award/54614
2012-11-05 17:06:00.000000||http://www.bco-dmo.org/award/54615
2016-08-20 03:10:00.000000|0.9|http://www.bco-dmo.org/dataset/546152
```