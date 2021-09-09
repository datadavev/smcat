function reportError(msg) {
    const ele = document.getElementById("errors");
    ele.innerText = ele.innerText + msg + "\n---\n";
}

function showMeta() {
    try {
        let ele = document.querySelector('script[type="application/ld+json"]')
        let meta = JSON.parse(ele.innerText);
        document.getElementById("jsonld").innerText = JSON.stringify(meta, null, 2);
    } catch (e) {
        reportError(e.message);
    }
}

async function embedLinked(item) {
    const url = item.attributes.getNamedItem("href").value;
    let response = await fetch(url);
    if (!response.ok) {
        throw new Error(`ERROR ${response.status} retrieving ${url}`);
    }
    let data = await response.json();
    let _head = document.getElementsByTagName("head").item(0);
    let ele = document.createElement("script");
    ele.setAttribute("type","application/ld+json");
    ele.appendChild(
        document.createTextNode(JSON.stringify(data, null, 2))
    )
    _head.appendChild(ele);
}

async function addMetadata() {
    let links = document.querySelectorAll('link[type="application/ld+json"]');
    let promises = [];
    for (let i=0; i < links.length; i++) {
        promises.push(embedLinked(links[i]));
    }
    await Promise.all(promises).catch(e => {
        reportError(e.message);
    })
    showMeta();
}

