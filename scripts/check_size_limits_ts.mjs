#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const frontend = path.join(root, "frontend");
const ts = createRequire(path.join(frontend, "package.json"))("typescript");
const FILE_MAX = 250;
const COMPONENT_MAX = 120;
const FUNC_MAX = 40;
const TEST_FILE_MAX = 300;
const EXEMPT = new Set();

function walk(dir, acc = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (entry.name === "node_modules" || entry.name === "dist") continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(full, acc);
    else if (/\.(ts|tsx)$/.test(entry.name)) acc.push(full);
  }
  return acc;
}

function span(node) {
  const sf = node.getSourceFile();
  const a = sf.getLineAndCharacterOfPosition(node.getStart(sf, false));
  const b = sf.getLineAndCharacterOfPosition(node.end);
  return b.line - a.line + 1;
}

function isComponent(name, node) {
  return Boolean(name && /^[A-Z]/.test(name)) &&
    (ts.isFunctionDeclaration(node) || ts.isFunctionExpression(node) || ts.isArrowFunction(node));
}

function check(filePath) {
  const rel = path.relative(root, filePath).split(path.sep).join("/");
  if (EXEMPT.has(rel)) return [];
  const source = fs.readFileSync(filePath, "utf8");
  const out = [];
  const lines = source ? source.split(/\r?\n/).length : 0;
  const test = rel.includes("/tests/") || /\.test\.(ts|tsx)$/.test(rel);
  if (lines > (test ? TEST_FILE_MAX : FILE_MAX)) {
    out.push(`${rel}: file has ${lines} lines (max ${test ? TEST_FILE_MAX : FILE_MAX})`);
  }
  const kind = filePath.endsWith(".tsx") ? ts.ScriptKind.TSX : ts.ScriptKind.TS;
  const sf = ts.createSourceFile(filePath, source, ts.ScriptTarget.Latest, true, kind);
  function visit(node, hinted) {
    const name = hinted || (node.name && ts.isIdentifier(node.name) ? node.name.text : undefined);
    const fn =
      ts.isFunctionDeclaration(node) ||
      ts.isMethodDeclaration(node) ||
      ts.isFunctionExpression(node) ||
      ts.isArrowFunction(node);
    if (fn) {
      const n = span(node);
      const component = isComponent(name, node);
      const max = component ? COMPONENT_MAX : FUNC_MAX;
      if (n > max) {
        const line = sf.getLineAndCharacterOfPosition(node.getStart()).line + 1;
        out.push(`${rel}:${line} ${component ? "component" : "function"} \`${name || "<anonymous>"}\` has ${n} lines (max ${max})`);
      }
    }
    if (ts.isVariableDeclaration(node) && ts.isIdentifier(node.name) && node.initializer) {
      visit(node.initializer, node.name.text);
      return;
    }
    ts.forEachChild(node, (child) => visit(child, undefined));
  }
  visit(sf, undefined);
  return out;
}

const violations = walk(path.join(frontend, "src"))
  .concat(walk(path.join(frontend, "tests")))
  .flatMap(check);
if (violations.length) {
  console.error("TypeScript size limit violations:");
  for (const item of violations) console.error(`  - ${item}`);
  process.exit(1);
}
console.log(`TypeScript size limits OK (file max ${FILE_MAX}, component max ${COMPONENT_MAX}, function max ${FUNC_MAX}).`);
