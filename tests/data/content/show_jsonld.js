import {LitElement, html, css} from "https://unpkg.com/lit-element@2.5.1/lit-element.js?module";

import * as jsonld from 'https://cdnjs.cloudflare.com/ajax/libs/jsonld/5.2.0/jsonld.min.js';

export class ShowJsonld extends LitElement {

  static get styles() {
    return css`
      :host {
        display: block;
        border: solid 1px gray;
        padding: 16px;
        max-width: 800px;
      }
    `;
  }

  static get properties() {
    return {
      use_proxy: {type: Boolean},
      location: {type: String},
      data: {type: Object},
      expanded: {type: Object},
      block_id: {type: Number},
      error: {type:String},
    };
  }

  constructor() {
    super();
    this._proxy_service = "https://thingproxy.freeboard.io/fetch/"
    this.use_proxy = false;
    this.location = ".";
    this.block_id = 0;
    this.data = {};
    this.error = "";
  }

  async loadRemote(url) {
    let _this = this;
    if (this.use_proxy) {
      url = `${this._proxy_service}${url}`;
    }
    fetch(url).then(response => response.text()).then(html => {
      const doc = new DOMParser().parseFromString(html, 'text/html');
      const eles = doc.querySelectorAll('script[type="application/ld+json"]');
      const _jsonld = JSON.parse(eles[_this.block_id].innerText);
      console.log(_jsonld);
      _this.data = _jsonld;
      window.jsonld.expand(_this.data).then(expanded => {
        _this.expanded = expanded;
      }).catch (error => {
        _this.error = error
      })

    }).catch(error => {
      _this.error = error;
    })
  }

  async connectedCallback() {
    super.connectedCallback();
    let _this = this;
    if (this.location === ".") {
      let eles = window.document.querySelectorAll('script[type="application/ld+json"]');
      try {
        this.data = JSON.parse(eles[this.block_id].innerText);
        window.jsonld.expand(this.data).then(expanded => {
          _this.expanded = expanded;
        }).catch (error => {
          _this.error = error
        })
      } catch (e) {
        this.data = `Error: could not render block ${this.block_id}: ${e}`;
      }
    } else {
      await this.loadRemote(this.location);
    }
  }



  render() {
    let errors = html``;
    if (this.error !== '') {
      errors = html`<pre>ERROR: ${this.error}</pre>`;
    }
    return html`
      <p>JsonLD Block ${this.location} # ${this.block_id}</p>
      <pre>${JSON.stringify(this.expanded,null,2)}</pre>
      ${errors}
    `;
  }
}

window.customElements.define('show-jsonld', ShowJsonld);