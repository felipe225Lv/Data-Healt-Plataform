// Lint sin dependencias: revisa la sintaxis de cada archivo JS con `node --check`
// y algunas reglas básicas de estilo.
import { execFileSync } from "node:child_process";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";

const roots = ["src", "scripts", "tests"];
const files = [];
const walk = (dir) => {
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) walk(path);
    else if (/\.(m?js)$/.test(name)) files.push(path);
  }
};
roots.forEach(walk);

let errors = 0;
for (const file of files) {
  try {
    execFileSync(process.execPath, ["--check", file], { stdio: "pipe" });
  } catch (err) {
    errors++;
    console.error(`✗ ${file}\n${err.stderr}`);
    continue;
  }
  readFileSync(file, "utf8").split("\n").forEach((line, i) => {
    if (/\bvar\s/.test(line)) { errors++; console.error(`✗ ${file}:${i + 1} usar let/const en lugar de var`); }
    if (/console\.log\(/.test(line) && file.startsWith("src")) { errors++; console.error(`✗ ${file}:${i + 1} console.log en código de la app`); }
    if (/\s+$/.test(line)) { errors++; console.error(`✗ ${file}:${i + 1} espacios al final de la línea`); }
  });
}

if (errors > 0) {
  console.error(`\nLint falló con ${errors} problema(s).`);
  process.exit(1);
}
console.log(`Lint OK: ${files.length} archivos revisados.`);
