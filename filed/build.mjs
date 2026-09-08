/* Bundles the prototype into a single self-contained page for publishing.
   Run: node build.mjs   →   dist/filed.html
   The output carries no <html>/<head>/<body> wrapper so it can be published
   as an Artifact; open index.html directly for the multi-file source. */

import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';

const read = (p) => readFileSync(new URL(p, import.meta.url), 'utf8');

const css = ['assets/tokens.css', 'assets/app.css'].map(read).join('\n');
const js  = ['assets/data.js', 'assets/ui.js', 'assets/screens-a.js', 'assets/screens-b.js', 'assets/screens-c.js', 'assets/app.js'].map(read).join('\n');

const out = `<title>FILED</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Sans:ital,wght@0,400..700;1,400..600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
${css}
</style>

<a class="skip" href="#main">Skip to content</a>
<div id="root"></div>
<div id="toasts" class="toasts" aria-live="polite"></div>

<script>
${js}
</script>
`;

mkdirSync(new URL('dist/', import.meta.url), { recursive: true });
writeFileSync(new URL('dist/filed.html', import.meta.url), out);
console.log(`dist/filed.html — ${(out.length / 1024).toFixed(0)} KB`);
