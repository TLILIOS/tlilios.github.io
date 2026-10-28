// scripts/serve-dist.mjs — serveur statique local pour valider dist/ (pa11y-ci).
// Sert les URLs propres (/x → /x/index.html). Usage validation uniquement, jamais déployé.
import http from "node:http";
import { readFile, stat } from "node:fs/promises";
import { join, extname, resolve } from "node:path";

const ROOT = resolve(process.cwd(), "dist");
const PORT = Number(process.env.PORT || 8788);
const MIME = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css",
  ".js": "text/javascript",
  ".json": "application/json",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".svg": "image/svg+xml",
  ".pdf": "application/pdf",
  ".mp4": "video/mp4",
  ".webp": "image/webp",
  ".ico": "image/x-icon",
  ".webmanifest": "application/manifest+json",
  ".vtt": "text/vtt",
  ".xml": "application/xml",
  ".txt": "text/plain",
};

const srv = http.createServer(async (req, res) => {
  const u = decodeURIComponent((req.url || "/").split("?")[0]);
  let f = join(ROOT, u);
  try {
    const s = await stat(f);
    if (s.isDirectory()) f = join(f, "index.html");
  } catch {
    try {
      await stat(join(f, "index.html"));
      f = join(f, "index.html");
    } catch {}
  }
  try {
    const data = await readFile(f);
    res.writeHead(200, { "Content-Type": MIME[extname(f)] || "application/octet-stream" });
    res.end(data);
  } catch {
    res.writeHead(404, { "Content-Type": "text/plain" });
    res.end("404");
  }
});
srv.listen(PORT, () => console.log(`serve-dist on http://localhost:${PORT}`));
