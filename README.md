# AGIChainAI — Official Website

The official website of **AGIChainAI** — decentralized infrastructure for the AGI era.

🌐 **Live site:** [www.agichainai.com](https://www.agichainai.com)

## About

AGIChainAI is an open, decentralized ecosystem combining artificial intelligence and blockchain: AI agents, a developer SDK, a marketplace, a wallet and a high-throughput chain — governed by its community through the AGIC utility token.

## Tech Stack

- **HTML5** — semantic, accessible markup
- **CSS3** — custom design system, glassmorphism, pure-CSS charts, no frameworks
- **Vanilla JavaScript** — zero dependencies, no build step

Hosted on **GitHub Pages** with a custom domain.

## Project Structure

```
agichainai-website/
├── index.html          # Homepage
├── style.css           # Complete design system
├── script.js           # All interactions & animations
├── 404.html            # Custom error page
├── CNAME               # Custom domain config
├── robots.txt          # Crawler rules
├── sitemap.xml         # SEO sitemap
├── manifest.json       # PWA manifest
├── browserconfig.xml   # Windows tile config
├── assets/             # Logo, favicon, backgrounds, icons
│   └── icons/
└── pages/              # Whitepaper, tokenomics, roadmap, FAQ, legal
```

## Running Locally

No build step required. Clone and open:

```bash
git clone https://github.com/aslanklc04/agichainai-website.git
cd agichainai-website
```

Then open `index.html` in your browser, or serve it locally:

```bash
python3 -m http.server 8000
# visit http://localhost:8000
```

## Deployment

The site deploys automatically via **GitHub Pages** from the `main` branch. Every push to `main` triggers a rebuild (usually live within 1–3 minutes).

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file.

## Links

- Website: https://www.agichainai.com
- Whitepaper: https://www.agichainai.com/pages/whitepaper.html
- Contact: hello@agichainai.com

---

*AGIC is a utility token. Nothing in this repository constitutes financial advice.*
