import { readFile, writeFile } from 'node:fs/promises'
const reportPath = 'records/REIN-HYBRID-20260914/bootstrap/integration-report.json'
const manifest = JSON.parse(await readFile('records/REIN-HYBRID-20260914/bootstrap/hybrid-tree-manifest.json', 'utf8'))
const original = JSON.parse(await readFile('records/REIN-HYBRID-20260914/bootstrap/original-file-manifest.json', 'utf8')).files
const imported = Object.keys(manifest.files).filter(path => !original[path] || original[path].sha256 !== manifest.files[path].sha256)
await writeFile('records/REIN-HYBRID-20260914/bootstrap/imported-paths.json', JSON.stringify({ count: imported.length, paths: imported }, null, 2) + '\n')
console.log(`recorded imported paths: ${imported.length}`)
