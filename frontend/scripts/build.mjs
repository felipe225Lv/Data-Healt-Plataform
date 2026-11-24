// Build del dashboard: copia src/ a dist/ y escribe la versión (commit) en el HTML.
import { cpSync, existsSync, readFileSync, rmSync, writeFileSync } from "node:fs";

const version = (process.env.GITHUB_SHA ?? process.env.BUILD_VERSION ?? "local").slice(0, 7);

if (existsSync("dist")) rmSync("dist", { recursive: true });
cpSync("src", "dist", { recursive: true });

const html = readFileSync("dist/index.html", "utf8");
if (!html.includes('id="build-version"')) {
  console.error("No se encontró el marcador de versión en index.html");
  process.exit(1);
}
writeFileSync("dist/index.html", html.replace('<span id="build-version">dev</span>', `<span id="build-version">${version}</span>`));
console.log(`Build OK en dist/ (versión ${version})`);
