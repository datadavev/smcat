# smcat
Sitemap cat


## Operation

Start up a test server:

```
python tests/tesetserver.py
```

Crawl the test data:

```
scrapy crawl LDSitemap -s SITEMAP_URLS=http://localhost:8001/robots.txt -a count_only=True
```

View the output:

```
cat items.jsonl | jq '.'
```

Examine sitemap alternate links:

```
scrapy crawl LDSitemap \
  -s SITEMAP_URLS=http://localhost:8001/sm02.xml \
  -s SITEMAP_ALTERNATE_LINKS=true \
  -a count_only=True
```
